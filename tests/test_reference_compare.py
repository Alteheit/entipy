from src.entipy import Reference, Field
from rapidfuzz import fuzz

# Setup

class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70


class SimpleProductReference(Reference):
    observed_name = ObservedNameField

class RetailStoreField(Field):
    value: str
    exclude = True

class CompoundProductReference(Reference):
    observed_name = ObservedNameField
    retail_store = RetailStoreField


r1 = SimpleProductReference(observed_name='PrimeHarvestCheese10Qg', metadata={'id': 1}) # A
r2 = SimpleProductReference(observed_name='PureGourCetYogurt2.4kg', metadata={'id': 2}) # B
r3 = SimpleProductReference(observed_name='PrimeHarvLstCheese1F0g', metadata={'id': 3}) # A
r4 = SimpleProductReference(observed_name='NutSaFusionBakingSoda200g', metadata={'id': 4}) # C
r5 = SimpleProductReference(observed_name='PrimeIarvestCh~ose100g', metadata={'id': 5}) # A
r6 = SimpleProductReference(observed_name='PureGotrmetYogurt2_4kg', metadata={'id': 6}) # B
r7 = SimpleProductReference(metadata={'id': 7}) # D

r8 = CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM', metadata={'id': 8}) # A
r9 = CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM', metadata={'id': 9}) # B

# Tests

def test_compare_same():
    assert r1.compare(r1) > 0

def test_compare_similar():
    assert r1.compare(r3) > 0

def test_compare_different():
    assert r1.compare(r2) < 0

def test_compare_commutative():
    assert r1.compare(r2) == r2.compare(r1)

def test_missing_field():
    assert r1.compare(r7) == 0

def test_exclude_field():
    assert r8.compare(r9) < 0
