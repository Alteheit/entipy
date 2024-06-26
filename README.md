# EntiPy
## By Hyperjoin

EntiPy is a Python toolkit that implements an incremental clustering approach to entity resolution. It is developed and maintained by Hyperjoin, and it is available under either the AGPLv3 license or a commercial license.

### Motivation

[Entity resolution](https://en.wikipedia.org/wiki/Record_linkage) (ER, also known as identity resolution, data deduplication, data matching, record linkage, merge-purge, and more) is the field concerned with grouping data records that are determined to point to the same real-world thing. The broad concept of ER has uses in master data management, customer data integration, and fraud detection.

ER is a difficult data problem. It is only necessary when matching data records do not share a common identifier, and if implemented naïvely, it is inherently quadratic in time complexity. Modern approaches to ER tend to be divided into three general phases:

- First, **data preprocessing**. Records from one or more data sources are transformed into a shape that later stages can consume.
- Second, **blocking**. If possible, any given record is tagged as possibly belonging to one or more subsets, or blocks, of records to avoid the need to compare each record against every other record. For example, ER on customers might be blocked by ZIP code.
- Third, **resolution**. Records within each block are compared against one another and are clustered based on their similarity to other records. Each cluster aims to be as close as possible to a real-world entity.

This library, EntiPy, implements **resolution** based on research done by [Tauer et al.](https://www.sciencedirect.com/science/article/abs/pii/S1566253517305729) and [Ilagan and Ilagan](https://www.dropbox.com/scl/fi/vwtta52zsyx5atpqoif80/1-ILAGAN_CENTERIS2023-1.pdf?rlkey=a8y2iucpjra02fepfomwl920k&dl=0).

## Prerequisites

- Python 3.10 or higher.
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

When resolution is complete, you can retrieve the dictionary forms of generated clusters with `.get_cluster_data()`, which returns a dictionary whose keys are arbitrary cluster IDs and whose values are lists of your `Reference` instances.

```python
clusters = resolver.get_cluster_data()
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

clusters = sr.get_cluster_data()
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

clusters = sr.get_cluster_data()
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
sr.get_cluster_data(include_reference_metadata=True)

''' Returns
{10: [{'metadata': '{"id": 4}', 'observed_name': 'NutSaFusionBakingSoda200g'}],
 12: [{'metadata': '{"id": 1}', 'observed_name': 'PrimeHarvestCheese10Qg'},
      {'metadata': '{"id": 3}', 'observed_name': 'PrimeHarvLstCheese1F0g'},
      {'metadata': '{"id": 5}', 'observed_name': 'PrimeIarvestCh~ose100g'}],
 14: [{'metadata': '{"id": 2}', 'observed_name': 'PureGourCetYogurt2.4kg'},
      {'metadata': '{"id": 6}', 'observed_name': 'PureGotrmetYogurt2_4kg'}]}
'''
```

### Blocking

Part of the complexity of entity resolution comes from the need to compare references to every other reference in the dataset. If left untreated, this results in a quadratic problem that even supercomputers and HPC clusters cannot solve. The most common remedy for this is to preemptively disqualify dissimilar references before even computing comparison scores. This is usually achieved by "blocking": whitelisting potentially-similar references instead of blacklisting dissimilar ones. Not all scenarios support blocking, but if your scenario does, use it; without blocking, ER is very difficult, if not impossible, to scale.

To demonstrate blocking, we will modify our tutorial scenario slightly. Our product name references will now also have a `retail_store` field. For the purposes of this tutorial, we will assume that products can only be sold in one retail store. This will make `retail_store` suitable to use as a blocking key, since we can assume that any two references that are _not_ in the same `retail_store` block are not coreferential.

You can define a `BlockingKey` in a similar way to defining `Fields`. `BlockingKeys` will be added as properties to your `Reference` later.

```python
from entipy import Reference, Field, SerialResolver, BlockingKey
from rapidfuzz import fuzz

class ObservedNameField(Field):
    ...


class RetailStoreField(Field):
    value: str
    # To exclude a field from comparison, set the `exclude` property to True.
    #  We will set exclude to True here because we are using this
    #  field as a blocking key, not as a probablistic comparison criterion.
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
```

Two clusters will only be compared if any reference within the first cluster shares any blocking key with any reference within the second cluster. If not, EntiPy will not waste compute comparing them.

Any of EntiPy's resolver classes will be able to handle references with blocking keys. As an example:

```python
references = [
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM'),
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM'),
    CompoundProductReference(observed_name='PrimeHarvLstCheese1F0g', retail_store='SM'),
    CompoundProductReference(observed_name='NutSaFusionBakingSoda200g', retail_store='SM'),
    CompoundProductReference(observed_name='PrimeIarvestCh~ose100g', retail_store='SM'),
    CompoundProductReference(observed_name='PureGotrmetYogurt2_4kg', retail_store='SM'),
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='SM'),
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='SM'),
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PrimeHarvLstCheese1F0g', retail_store='Robinsons'),
    CompoundProductReference(observed_name='NutSaFusionBakingSoda200g', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PrimeIarvestCh~ose100g', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PureGotrmetYogurt2_4kg', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PrimeHarvestCheese10Qg', retail_store='Robinsons'),
    CompoundProductReference(observed_name='PureGourCetYogurt2.4kg', retail_store='Robinsons'),
]

sr = SerialResolver(references)

sr.resolve()

sr.get_cluster_data()

'''
Should yield:
{20: [{'observed_name': 'NutSaFusionBakingSoda200g', 'retail_store': 'SM'}],
 26: [{'observed_name': 'PrimeHarvestCheese10Qg', 'retail_store': 'SM'},
      {'observed_name': 'PrimeHarvLstCheese1F0g', 'retail_store': 'SM'},
      {'observed_name': 'PrimeIarvestCh~ose100g', 'retail_store': 'SM'},
      {'observed_name': 'PrimeHarvestCheese10Qg', 'retail_store': 'SM'}],
 28: [{'observed_name': 'PureGourCetYogurt2.4kg', 'retail_store': 'SM'},
      {'observed_name': 'PureGotrmetYogurt2_4kg', 'retail_store': 'SM'},
      {'observed_name': 'PureGourCetYogurt2.4kg', 'retail_store': 'SM'}],
 33: [{'observed_name': 'NutSaFusionBakingSoda200g',
       'retail_store': 'Robinsons'}],
 39: [{'observed_name': 'PrimeHarvestCheese10Qg', 'retail_store': 'Robinsons'},
      {'observed_name': 'PrimeHarvLstCheese1F0g', 'retail_store': 'Robinsons'},
      {'observed_name': 'PrimeIarvestCh~ose100g', 'retail_store': 'Robinsons'},
      {'observed_name': 'PrimeHarvestCheese10Qg', 'retail_store': 'Robinsons'}],
 41: [{'observed_name': 'PureGourCetYogurt2.4kg', 'retail_store': 'Robinsons'},
      {'observed_name': 'PureGotrmetYogurt2_4kg', 'retail_store': 'Robinsons'},
      {'observed_name': 'PureGourCetYogurt2.4kg', 'retail_store': 'Robinsons'}]}
'''
```

Please note that blocking is meant to disqualify obviously dissimilar references, not to narrow down possibly similar references. Adding more blocking keys actually _increases_ the number of comparisons that EntiPy must execute, so design your blocking strategy accordingly.

### Speeding up resolution with MergeResolver

EntiPy provides a more advanced resolver called the `MergeResolver` that parallelizes resolution even without blocks. Its interface is the same as `SerialResolver`, but internally, it implements a mergesort-inspired resolution algorithm. Resolution results are mostly similar to `SerialResolver` results, but are computed _much_ faster.

```python
from entipy import Field, Reference, MergeResolver
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

'''
clusters should contain:

{16: [{'observed_name': 'NutSaFusionBakingSoda200g'}],
 18: [{'observed_name': 'PrimeHarvestCheese10Qg'},
  {'observed_name': 'PrimeHarvLstCheese1F0g'},
  {'observed_name': 'PrimeIarvestCh~ose100g'}],
 20: [{'observed_name': 'PureGourCetYogurt2.4kg'},
  {'observed_name': 'PureGotrmetYogurt2_4kg'}]}
'''
```
Playing around with MergeResolver in the product name resolution demo brings resolution time for 4350 records down from 8 minutes (bad) to 1 minute (less bad) without parallelizing the work. If parallelized, the time can be even lower.

### Other demonstrations

Other demonstrations may be found in the `demos/` folder of this repository. We recommend trying the `product_name_resolution` demo to understand what motivated the development of EntiPy.

## Q\&A

**Q: Can I mix different types of References in one Resolver?**

**A:** EntiPy is not built to handle heterogeneous References in one Resolver. Please use only one schema within one Resolver as much as possible.

**Q: My resolution is going really slowly. What can I do to improve it?**

**A:** A cheap way to increase performance is to use MergeResolver if possible. This should work on all types of data. However, the most drastic performance gains by far come from blocking.

In my initial tests on product name data:

- SerialResolver with no blocking: 8 minutes
- MergeResolver with no blocking and no parallelization: 1 minute
- MergeResolver with blocking on the first character: 4 seconds (!)

## Roadmap

EntiPy is currently in pre-alpha. Do not expect the API to remain stable.

The EntiPy project aims to implement the following features in future versions:

- True parallel resolution for MergeResolver
- Indexing references on metadata, which will enable use cases like search
- Cluster assertion, i.e., allowing manual assertion that references should be clustered
- Weak cluster dispersion
- Using disks/databases

It is not the aim of EntiPy to implement similarity functions for fields.

## Copyright and license

© 2024 Joe Ilagan. All rights reserved.

By default, EntiPy is licensed under the GNU Affero General Public License version 3 (AGPLv3). If you would like to use EntiPy for a project that cannot abide by the terms of AGPLv3, please contact us to purchase a commercial license, payable to Archmob Pte. Ltd.

## Contributions

EntiPy is not currently accepting contributions. This may change once the use cases of the project develop.

## Contact

The author and maintainer of this library is Joe Ilagan. He can be reached at joe@archmob.com.
