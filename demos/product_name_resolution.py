from src.entipy import Field, Reference, SerialResolver
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


class ProductNameReference(Reference):
    observed_name = ObservedNameField


# Load product names
with open('samples/product-name-demo-dataset.csv') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = [l for l in reader]
    observed_names = [x[0] for x in rows]

references = [ProductNameReference(observed_name=x) for x in observed_names]

sr = SerialResolver(references)

sr.resolve(verbose=True)

# with open('demo-result.json', 'w') as f:
#     json.dump(sr.retrieve_clusters(), f, indent=4, sort_keys=True)

end = dt.datetime.now()

print(f'Elapsed: {end - start}')
