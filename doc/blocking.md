# Blocking

## Scratch

- Most blocking techniques are applied at the reference-pair level
- IGP algorithm applies blocking at the cluster level
- Ok, how exactly does this work?
    - "When a blocking strategy is applied, the algorithm will only compute a cluster-pair weightsum when at least one reference in the first cluster and one reference in the second cluster satisfies the blocking condition"
    - So wait. Does this mean that, assuming you start from only single references, that per cluster, there will only be one bk_value per bk_name? Does that imply that a Cluster can have its own internal BK metadata?
    - I'm fairly confident that a *Reference* will have a one-layer dictionary for {bk_name: bk_value}
        - This is expressed in its blocking_keys instance attribute
    - A Cluster is composed of many References
        - It might make sense to get the union of the blocking_keys dicts of all the References. This does assume that no one blocking key will have conflicting values, only that References might have missing blocking keys
    - To my understanding, this simplifies the problem:
        - When a Cluster is created, say from one Reference, add the Reference's blocking keys to the Cluster's blocking keys
        - When a Cluster is merged with another Cluster, we should expect a conflict-free union between Cluster 1's blocking keys and Cluster 2's blocking keys
            - This also applies to adding a single Reference to a Cluster, since this simplifies to wrapping the Reference as a one-Reference Cluster and then merging the two Clusters
            - If it isn't conflict-free, then the blocking broke somewhere
        - When Clusters are compared, the comparison should only go through if they share _at least one_ blocking key-value

- Do we even have to get to the comparison step?
    - Shouldn't the Resolvers just index which clusters belong to which blocks
    - Ok actually somewhat harder than I thought, I'll just put the check in the comparison step for now

- Maybe keep it at the comparison step for now yeah
    - I had a fundamental misunderstanding of how blocking works
    - "If Clusters share ANY blocking key, they must be compared; if not, then not."
    - It's more of to disqualify obviously dissimilar refs than to qualify potentially similar ones
    - Any, not all
        - Does this affect the implementation in Cluster?

- References within a Cluster will not necessarily all share the same BK apparently...
    - So Refs can have strings for their BKVs, but Clusters must have {BKN: set[BKV]}
    - God dammit
