package org.blagodarie;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableField;
import androidx.lifecycle.ViewModel;

import java.util.HashSet;
import java.util.Set;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainViewModel
        extends ViewModel {

    public ObservableField<String> mLocation = new ObservableField<>("");

    @NonNull
    private final Set<DisplaySymptom> mSymptoms = new HashSet<>();

    {
        for (Symptom symptom : Symptom.getSymptoms()) {
            mSymptoms.add(new DisplaySymptom(symptom));
        }
    }

    public MainViewModel () {
        super();
    }

    final Set<DisplaySymptom> getSymptoms () {
        return mSymptoms;
    }
}
