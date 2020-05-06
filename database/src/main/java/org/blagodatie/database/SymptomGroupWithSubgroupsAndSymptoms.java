package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.room.Embedded;
import androidx.room.Relation;

import java.util.List;

public final class SymptomGroupWithSubgroupsAndSymptoms {

    @NonNull
    @Embedded
    private final SymptomGroup SymptomGroup;

    @NonNull
    @Relation (
            parentColumn = "id",
            entityColumn = "parent_id",
            entity = SymptomGroup.class
    )
    private final List<SymptomGroup> Subgroups;

    @NonNull
    @Relation (
            parentColumn = "id",
            entityColumn = "group_id",
            entity = Symptom.class
    )
    private final List<Symptom> Symptoms;

    SymptomGroupWithSubgroupsAndSymptoms (
            @NonNull final SymptomGroup SymptomGroup,
            @NonNull final List<Symptom> Symptoms,
            @NonNull final List<SymptomGroup> Subgroups
    ) {
        this.SymptomGroup = SymptomGroup;
        this.Symptoms = Symptoms;
        this.Subgroups = Subgroups;
    }
}
