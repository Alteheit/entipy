from src.entipy import Reference, Field
from rapidfuzz import fuzz

# Setup

class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70


class ProductNameReference(Reference):
    observed_name = ObservedNameField


r1 = ProductNameReference(observed_name='PrimeHarvestCheese10Qg', metadata={'id': 1}) # A
r2 = ProductNameReference(observed_name='PureGourCetYogurt2.4kg', metadata={'id': 2}) # B
r3 = ProductNameReference(observed_name='PrimeHarvLstCheese1F0g', metadata={'id': 3}) # A
r4 = ProductNameReference(observed_name='NutSaFusionBakingSoda200g', metadata={'id': 4}) # C
r5 = ProductNameReference(observed_name='PrimeIarvestCh~ose100g', metadata={'id': 5}) # A
r6 = ProductNameReference(observed_name='PureGotrmetYogurt2_4kg', metadata={'id': 6}) # B
r7 = ProductNameReference(metadata={'id': 7}) # D

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
