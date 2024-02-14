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

Once you have modeled your reference class, you can use it to create Reference objects like so:

```python
ref_1 = ProductNameReference(observed_name="PrimeHarvestCheese10Qg")
ref_2 = ProductNameReference(observed_name="PureGourCetYogurt2.4kg")
ref_3 = ProductNameReference(observed_name="PrimeHarvLstCheese1F0g")
```

Your reference objects can then be used with the `SerialResolver` entity resolution engine, which we will discuss next.

### Implementing entity resolution with the SerialResolver

The central building block of EntiPy is the `SerialResolver`. This class is a stateful and thread-unsafe agent that clusters data records.

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

## License

By default, EntiPy is licensed under the GNU General Public License version 3 (GPLv3). If you would like to use EntiPy for a project that cannot abide by the terms of GPLv3, please contact us to purchase a commercial license, payable to Archmob Pte. Ltd.

## Contact

The principal author and maintainer of this library is Joe Ilagan. He can be reached at joe@archmob.com.
