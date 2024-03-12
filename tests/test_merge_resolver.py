from src.entipy import Field, Reference, MergeResolver
from rapidfuzz import fuzz


class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70


class ProductNameReference(Reference):
    observed_name = ObservedNameField


r1 = ProductNameReference(observed_name='PrimeHarvestCheese10Qg')
r2 = ProductNameReference(observed_name='PureGourCetYogurt2.4kg')
r3 = ProductNameReference(observed_name='PrimeHarvLstCheese1F0g')
r4 = ProductNameReference(observed_name='NutSaFusionBakingSoda200g')
r5 = ProductNameReference(observed_name='PrimeIarvestCh~ose100g')
r6 = ProductNameReference(observed_name='PureGotrmetYogurt2_4kg')

mr = MergeResolver([r1, r2, r3, r4, r5, r6])

mr.resolve()

clusters = mr.get_cluster_data()
