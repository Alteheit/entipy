from src.entipy import Field, Reference, SerialResolver
from rapidfuzz import fuzz
from pprint import pprint


class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70


class ProductNameReference(Reference):
    observed_name = ObservedNameField


r1 = ProductNameReference(observed_name='PrimeHarvestCheese10Qg', metadata={'id': 1})
r2 = ProductNameReference(observed_name='PureGourCetYogurt2.4kg', metadata={'id': 2})
r3 = ProductNameReference(observed_name='PrimeHarvLstCheese1F0g', metadata={'id': 3})
r4 = ProductNameReference(observed_name='NutSaFusionBakingSoda200g', metadata={'id': 4})
r5 = ProductNameReference(observed_name='PrimeIarvestCh~ose100g', metadata={'id': 5})
r6 = ProductNameReference(observed_name='PureGotrmetYogurt2_4kg', metadata={'id': 6})

sr = SerialResolver([r1, r2, r3, r4, r5, r6])

sr.resolve(verbose=True)

pprint(sr.retrieve_clusters(include_reference_metadata=True))

# Adding another Reference

r7 = ProductNameReference(observed_name='PureGourmetCookinMOil300mL', metadata={'id': 7})

sr.add(r7)

sr.resolve(verbose=True)

r8 = ProductNameReference(observed_name='DeliFresqeoyXauce1L', metadata={'id': 8})
r9 = ProductNameReference(observed_name='DeliFreshSoySakcE1.2L', metadata={'id': 9})

sr.add([r8, r9])

sr.resolve(verbose=True)

pprint(sr.retrieve_clusters(include_reference_metadata=True))
