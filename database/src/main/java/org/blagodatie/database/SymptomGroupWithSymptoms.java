package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.room.Embedded;
import androidx.room.Relation;

import java.util.List;

public final class SymptomGroupWithSymptoms {

    @NonNull
    @Embedded
    private final SymptomGroup SymptomGroup;

    @NonNull
    @Relation (
            parentColumn = "id",
            entityColumn = "group_id",
            entity = Symptom.class
    )
    private final List<Symptom> Symptoms;

    SymptomGroupWithSymptoms (
            @NonNull final SymptomGroup SymptomGroup,
            @NonNull final List<Symptom> Symptoms
    ) {
        this.SymptomGroup = SymptomGroup;
        this.Symptoms = Symptoms;
    }

    @NonNull
    public final SymptomGroup getSymptomGroup () {
        return SymptomGroup;
    }

    @NonNull
    public final List<Symptom> getSymptoms () {
        return Symptoms;
    }
}
