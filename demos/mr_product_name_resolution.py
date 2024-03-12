from src.entipy import Field, Reference, SerialResolver, MergeResolver, BlockingKey
import csv
import json
from rapidfuzz import fuzz
import datetime as dt

start = dt.datetime.now()

class ObservedNameField(Field):
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other):
        return fuzz.ratio(self.value, other.value) >= 70

class EndCharactersBK(BlockingKey):
    name = 'ECBK'
    def compute(self):
        return f'''{self.reference.observed_name.value[0]}{self.reference.observed_name.value[-1]}'''

class FirstCharacterBK(BlockingKey):
    name = 'FCBK'
    def compute(self):
        return self.reference.observed_name.value[0]

class LastCharacterBK(BlockingKey):
    name = 'LCBK'
    def compute(self):
        return self.reference.observed_name.value[-1]


class ProductNameReference(Reference):
    observed_name = ObservedNameField
    first_character_bk = FirstCharacterBK
    last_character_bk = LastCharacterBK


# Load product names
with open('samples/product-name-demo-dataset.csv') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = [l for l in reader]
    observed_names = [x[1] for x in rows]

references = [ProductNameReference(observed_name=x) for x in observed_names]

mr = MergeResolver(references)

mr.resolve(verbose=True)

with open('demo-result.json', 'w') as f:
    json.dump(mr.get_cluster_data(), f, indent=4, sort_keys=True)

end = dt.datetime.now()

print(f'Elapsed: {end - start}')
