from src.entipy import Reference, Field, BlockingKey
from src.entipy.datamodels import Cluster
from rapidfuzz import fuzz

# Setup

class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70

class RetailStoreField(Field):
    value: str
    exclude = True

class RetailStoreBK(BlockingKey):
    # BlockingKeys may be expected to contain a reference to their Reference object.
    # You can use this property in the `compute` method.
    reference: Reference
    # BlockingKeys are expected to have a name
    name = 'RSBK' # Let's set this to "RSBK" for brevity
    def compute(self):
        # BlockingKeys are expected to have a `compute` method.
        #  `compute` will return the value of the blocking key
        #  based on the attributes of their Reference.
        # In this case, we will simply use the raw value of the
        #  `retail_store` field.
        return self.reference.retail_store.value

class CompoundProductReference(Reference):
    observed_name = ObservedNameField
    retail_store = RetailStoreField
    retail_store_bk = RetailStoreBK

r1 = CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM', metadata={'id': 1}) # A
r2 = CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM', metadata={'id': 2}) # B
r3 = CompoundProductReference(observed_name='PrimeHarvLstCheese1F0g', retail_store='Robinsons', metadata={'id': 3}) # C

c1 = Cluster(set([r1]))
c2 = Cluster(set([r2]))
c3 = Cluster(set([r3]))

c4 = Cluster(set([r1, r2, r3]))

# Tests

def test_reference_blocking_key():
    assert r1.blocking_keys['RSBK'] == 'SM'
    assert r3.blocking_keys['RSBK'] == 'Robinsons'
    assert not (r1.blocking_keys['RSBK'] == 'Robinsons')

def test_cluster_blocking_keys():
    assert c1.blocking_keys['RSBK'] == {'SM',}
    assert c1.merge(c2).blocking_keys['RSBK'] == {'SM',}

def test_clusters_have_common_block():
    assert c1.has_common_block(c2)
    assert not c1.has_common_block(c3)

def test_cluster_has_set_bkvs():
    print(c4.blocking_keys)
    assert c4.blocking_keys['RSBK'] == {'SM', 'Robinsons'}

# Setup

class SimpleProductReference(Reference):
    observed_name = ObservedNameField

r4 = SimpleProductReference(observed_name='PrimeHarvestCheese10Qg') # A
c5 = Cluster(set([r4]))

# Tests

def test_dummy_blocking_key():
    c5.blocking_keys['BK'] == '0'
