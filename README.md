# EntiPy

EntiPy is a Python library that implements an incremental clustering approach to entity resolution.

### Motivation

[Entity resolution](https://en.wikipedia.org/wiki/Record_linkage) (ER, also known as identity resolution, data deduplication, data matching, record linkage, merge-purge, and more) is the field concerned with grouping data records that are determined to point to the same real-world thing. The broad concept of ER has uses in master data management, customer data integration, and fraud detection.

ER is a difficult data problem. It is only necessary when matching data records do not share a common identifier, and if implemented naïvely, it is inherently quadratic in time complexity. Modern approaches to ER tend to be divided into three general phases:

- First, **data preprocessing**. Records from one or more data sources are transformed into a shape that later stages can consume.
- Second, **blocking**. If possible, any given record is tagged as possibly belonging to one or more subsets, or blocks, of records to avoid the need to compare each record against every other record. For example, ER on customers might be blocked by ZIP code.
- Third, **resolution**. Records within each block are compared against one another and are clustered based on their similarity to other records. Each cluster aims to be as close as possible to a real-world entity.

This library, EntiPy, implements **resolution** based on research done by [Tauer et al.](https://www.sciencedirect.com/science/article/abs/pii/S1566253517305729) and [Ilagan and Ilagan](#).

## Prerequisites

- Python 3.11 or higher.
    - We built and tested this version of EntiPy with Python 3.11.2.
- `sortedcontainers`
    - Your Python environment must be able to install and use the `sortedcontainers` library, which can be found [here](https://github.com/grantjenks/python-sortedcontainers).

## Installation

You can install EntiPy with `pip`. We recommend installing EntiPy in a virtual environment.

```bash
pip install entipy
```

## Getting Started

EntiPy's primary focus is on implementing the resolution algorithm, which means that you will need to model your data upfront. We provide tools and documentation to help you with this data modeling.

In this tutorial, a data record will be a potentially-misspelled product name that was read from an OCR scan. To cluster these records is thus to resolve them to the real, underlying products behind the observed product name.

### Modeling your data with References and Fields

We first need to define a data record type. We will call the overall shape of a data record a `Reference`. A `Reference` will have one or more field properties.

```python
from entipy import Reference, Field

class ProductNameReference(Reference):
    observed_name: Field
```

Fields represent the different properties of a data record. A field class inherits from the generic `Field` class. Your custom field class will need to implement one method, `compare`, which will return whether or not a field instance should be considered to match with another field instance. You can use the `value` property of the generic `Field` class as the basis for this comparison.

```python
from entipy import Reference, Field
from rapidfuzz import fuzz

class ProductNameReference(Reference):
    observed_name: Field

class ObservedNameField(Field):
    value: str
    def compare(self, other) -> bool:
        return fuzz.ratio(self.value, other.value) >= 70
```

A field class also has two additional properties. The float `true_match_probability` represents the probability that two coreferential `References` will match on the field. The float `false_match_probability` represents the probability that two non-coreferential `References` will match on the field. The default value for `true_match_probability` is `0.9`, and the default value for `false_match_probability` is `0.1`. It is likely that you will need to change these values for each field, which you can do as such:

```python
from entipy import Reference, Field
from rapidfuzz import fuzz

class ProductNameReference(Reference):
    observed_name: Field

class ObservedNameField(Field):
    value: str
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other) -> bool:
        return fuzz.ratio(self.value, other.value) >= 70
```

Once you have modeled your field class, you can replace the type annotation in your `ProductNameReference` class with your custom `ObservedNameField` class.

```python
from entipy import Reference, Field
from rapidfuzz import fuzz

# Note that we placed the field class first to satisfy the Python interpreter
class ObservedNameField(Field):
    value: str # This line is optional. It indicates that Field inheritors are expected to have a `value` property.
    true_match_probability = 0.85
    false_match_probability = 0.15
    def compare(self, other) -> bool:
        return fuzz.ratio(self.value, other.value) >= 70

class ProductNameReference(Reference):
    # Please note that you must assign the class of a Field model itself to a property name on your Reference model.
    observed_name = ObservedNameField
```

Once you have modeled your reference class, you can use it to create Reference objects like so. Your Reference objects can be instantiated with kwargs. The value of each kwarg should be the value you intend the respective Field to take.

```python
ref_1 = ProductNameReference(observed_name="PrimeHarvestCheese10Qg")
ref_2 = ProductNameReference(observed_name="PureGourCetYogurt2.4kg")
ref_3 = ProductNameReference(observed_name="PrimeHarvLstCheese1F0g")
```

Your reference objects can then be used with the `SerialResolver` entity resolution engine, which we will discuss next.

### Implementing entity resolution with the SerialResolver

The central building block of EntiPy is the `SerialResolver`. This class represents a stateful agent that clusters data records serially.

At a basic level, the `SerialResolver` accepts a sequence (a list or a set) of references when first instantiated.

```python
from entipy import Reference, Field, SerialResolver

...

resolver = SerialResolver([r1, r2, r3])
```

You can then call the `.resolve()` method of the `SerialResolver` to begin entity resolution. This will make the `SerialResolver` process the `Reference` inheritors inplace.

```python
resolver.resolve()
```

When resolution is complete, you can retrieve the generated clusters with `.retrieve_clusters()`, which returns a dictionary whose keys are arbitrary cluster IDs and whose values are lists of your `Reference` instances.

```python
clusters = resolver.retrieve_clusters()
```

### A working demonstration

We can tie everything we have seen so far into a short working demonstration of resolving a small batch of references.

```python
from entipy import Field, Reference, SerialResolver
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

sr = SerialResolver([r1, r2, r3, r4, r5, r6])

sr.resolve()

clusters = sr.retrieve_clusters()
```

The `clusters` variable should look something like this:

```python
{10: [{'observed_name': 'NutSaFusionBakingSoda200g'}],
 12: [{'observed_name': 'PrimeHarvestCheese10Qg'},
  {'observed_name': 'PrimeHarvLstCheese1F0g'},
  {'observed_name': 'PrimeIarvestCh~ose100g'}],
 14: [{'observed_name': 'PureGourCetYogurt2.4kg'},
  {'observed_name': 'PureGotrmetYogurt2_4kg'}]}
```

### Incremental resolution

A key feature of EntiPy is its ability to incrementally resolve references that arrive after the initial batch. `SerialResolvers` support adding either single references or lists of references through its `.add()` method.

```python
r7 = ProductNameReference(observed_name='PureGourmetCookinMOil300mL')

sr.add(r7)

sr.resolve()

r8 = ProductNameReference(observed_name='DeliFresqeoyXauce1L')
r9 = ProductNameReference(observed_name='DeliFreshSoySakcE1.2L')

sr.add([r8, r9])

sr.resolve()

clusters = sr.retrieve_clusters()
```

The `clusters` variable should now look something like this:

```python
{10: [{'observed_name': 'NutSaFusionBakingSoda200g'}],
 12: [{'observed_name': 'PrimeHarvestCheese10Qg'},
      {'observed_name': 'PrimeHarvLstCheese1F0g'},
      {'observed_name': 'PrimeIarvestCh~ose100g'}],
 14: [{'observed_name': 'PureGourCetYogurt2.4kg'},
      {'observed_name': 'PureGotrmetYogurt2_4kg'}],
 16: [{'observed_name': 'PureGourmetCookinMOil300mL'}],
 21: [{'observed_name': 'DeliFresqeoyXauce1L'},
      {'observed_name': 'DeliFreshSoySakcE1.2L'}]}
```

### Including Reference metadata

When instantiating a Reference, you can assign a dictionary to the `metadata` kwarg. This is useful for knowing which row a Reference was sourced from and for managing similar tracking data.

```python
r1 = ProductNameReference(observed_name='PrimeHarvestCheese10Qg', metadata={'id': 1})
r2 = ProductNameReference(observed_name='PureGourCetYogurt2.4kg', metadata={'id': 2})
r3 = ProductNameReference(observed_name='PrimeHarvLstCheese1F0g', metadata={'id': 3})
r4 = ProductNameReference(observed_name='NutSaFusionBakingSoda200g', metadata={'id': 4})
r5 = ProductNameReference(observed_name='PrimeIarvestCh~ose100g', metadata={'id': 5})
r6 = ProductNameReference(observed_name='PureGotrmetYogurt2_4kg', metadata={'id': 6})
```

The metadata dictionary must be JSON-serializable. Data assigned to the `metadata` kwarg in this way will remain attached to the reference as it is processed by EntiPy's resolvers, but it will not be included in reference comparisons.

When retrieving clusters from a `SerialResolver`, you can toggle whether reference metadata should be included in the dictionary representation of your clusters with the `include_reference_metadata` keyword. This kwarg is `False` by default.

```python
sr.retrieve_clusters(include_reference_metadata=True)

''' Returns
{10: [{'metadata': '{"id": 4}', 'observed_name': 'NutSaFusionBakingSoda200g'}],
 12: [{'metadata': '{"id": 1}', 'observed_name': 'PrimeHarvestCheese10Qg'},
      {'metadata': '{"id": 3}', 'observed_name': 'PrimeHarvLstCheese1F0g'},
      {'metadata': '{"id": 5}', 'observed_name': 'PrimeIarvestCh~ose100g'}],
 14: [{'metadata': '{"id": 2}', 'observed_name': 'PureGourCetYogurt2.4kg'},
      {'metadata': '{"id": 6}', 'observed_name': 'PureGotrmetYogurt2_4kg'}]}
'''
```

### Other demonstrations

Other demonstrations may be found in the `demos/` folder of this repository. We recommend trying the `product_name_resolution` demo to understand what motivated the development of EntiPy.

## Roadmap

EntiPy is currently in pre-alpha. Do not expect the API to remain stable.

The EntiPy project aims to implement the following features in future versions:
- Blocking
- Parallel resolution
- Weak cluster dispersion

It is not the aim of EntiPy to implement similarity functions for fields.

## License

By default, EntiPy is licensed under the GNU Affero General Public License version 3 (AGPLv3). If you would like to use EntiPy for a project that cannot abide by the terms of AGPLv3, please contact us to purchase a commercial license, payable to Archmob Pte. Ltd.

## Contributions

EntiPy is not currently accepting contributions. This may change once the use cases of the project develop.

## Contact

The author and maintainer of this library is Joe Ilagan. He can be reached at joe@archmob.com.
