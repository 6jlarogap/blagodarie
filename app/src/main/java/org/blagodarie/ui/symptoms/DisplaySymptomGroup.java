package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;

import org.blagodarie.BR;
import org.blagodatie.database.Identifier;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public final class DisplaySymptomGroup
        extends BaseObservable {


    @NonNull
    private final String mSymptomGroupName;

    @NonNull
    private final List<DisplaySymptom> mDisplaySymptoms = new ArrayList<>();

    private boolean mSelected = false;

    DisplaySymptomGroup (
            @NonNull final String symptomGroupName,
            @NonNull final List<DisplaySymptom> displaySymptoms
    ) {
        mSymptomGroupName = symptomGroupName;
        mDisplaySymptoms.addAll(displaySymptoms);
    }

    @NonNull
    public String getSymptomGroupName () {
        return mSymptomGroupName;
    }

    @NonNull
    List<DisplaySymptom> getDisplaySymptoms () {
        return mDisplaySymptoms;
    }

    @Bindable
    public boolean isSelected () {
        return mSelected;
    }

    void setSelected (final boolean selected) {
        mSelected = selected;
        notifyPropertyChanged(org.blagodarie.BR.selected);
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplaySymptomGroup that = (DisplaySymptomGroup) o;
        return mSelected == that.mSelected &&
                mSymptomGroupName.equals(that.mSymptomGroupName) &&
                mDisplaySymptoms.equals(that.mDisplaySymptoms);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mSymptomGroupName, mDisplaySymptoms, mSelected);
    }

    @Override
    public String toString () {
        return "DisplaySymptomGroup{" +
                ", mSymptomGroupName='" + mSymptomGroupName + '\'' +
                ", mDisplaySymptoms=" + mDisplaySymptoms +
                ", mSelected=" + mSelected +
                '}';
    }
}
