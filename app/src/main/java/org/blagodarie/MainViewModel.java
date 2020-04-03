package org.blagodarie;

import androidx.annotation.NonNull;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import java.util.HashSet;
import java.util.Set;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainViewModel
        extends ViewModel {

    @NonNull
    private final MutableLiveData<Set<DisplaySymptom>> mSymptoms = new MutableLiveData<>();

    {
        final Set<DisplaySymptom> symptomTreeSet = new HashSet<>();
        for (Symptom symptom : Symptom.getSymptoms()) {
            symptomTreeSet.add(new DisplaySymptom(symptom));
        }
        mSymptoms.setValue(symptomTreeSet);
    }

    public MainViewModel () {
        super();
    }

    final MutableLiveData<Set<DisplaySymptom>> getSymptoms () {
        return mSymptoms;
    }
}
