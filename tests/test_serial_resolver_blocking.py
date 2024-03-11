from src.entipy import Reference, Field, BlockingKey, SerialResolver
from src.entipy.datamodels import Cluster
from rapidfuzz import fuzz
from pprint import pprint

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

references = [
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM', metadata={'id': 1}), # A
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM', metadata={'id': 2}), # B
    CompoundProductReference(observed_name='PrimeHarvLstCheese1F0g', retail_store='SM', metadata={'id': 3}), # A
    CompoundProductReference(observed_name='NutSaFusionBakingSoda200g', retail_store='SM', metadata={'id': 4}), # C
    CompoundProductReference(observed_name='PrimeIarvestCh~ose100g', retail_store='SM', metadata={'id': 5}), # A
    CompoundProductReference(observed_name='PureGotrmetYogurt2_4kg', retail_store='SM', metadata={'id': 6}), # B
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM', metadata={'id': 8}), # A
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM', metadata={'id': 9}), # B

    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='Robinsons', metadata={'id': 1}), # A
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='Robinsons', metadata={'id': 2}), # B
    CompoundProductReference(observed_name='PrimeHarvLstCheese1F0g', retail_store='Robinsons', metadata={'id': 3}), # A
    CompoundProductReference(observed_name='NutSaFusionBakingSoda200g', retail_store='Robinsons', metadata={'id': 4}), # C
    CompoundProductReference(observed_name='PrimeIarvestCh~ose100g', retail_store='Robinsons', metadata={'id': 5}), # A
    CompoundProductReference(observed_name='PureGotrmetYogurt2_4kg', retail_store='Robinsons', metadata={'id': 6}), # B
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='Robinsons', metadata={'id': 8}), # A
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='Robinsons', metadata={'id': 9}), # B
]

sr = SerialResolver(references)

sr.resolve()

pprint(sr.get_cluster_data())

# Tests

def test_no_block_mixing_with_one_bk():
    clusters = sr.get_cluster_data()
    for k, v in clusters.items():
        retail_store_set = set(v2['retail_store'] for v2 in v)
        assert len(retail_store_set) == 1
