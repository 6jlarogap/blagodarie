package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;

import org.blagodatie.database.SymptomGroup;

interface SymptomGroupClickListener {

    void onClick (
            @NonNull final DisplaySymptomGroup displaySymptomGroup
    );

}
