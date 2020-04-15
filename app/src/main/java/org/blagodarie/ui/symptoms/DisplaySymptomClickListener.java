package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;

import org.blagodarie.ui.symptoms.DisplaySymptom;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
interface DisplaySymptomClickListener {
    void onClick (
            @NonNull final DisplaySymptom displaySymptom
    );
}
