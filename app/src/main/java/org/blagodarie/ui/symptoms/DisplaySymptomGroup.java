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
    private final Identifier mSymptomGroupId;

    @NonNull
    private final String mSymptomGroupName;

    @NonNull
    private final List<DisplaySymptom> mDisplaySymptoms = new ArrayList<>();

    private boolean mSelected = false;

    DisplaySymptomGroup (
            @NonNull final Identifier symptomGroupId,
            @NonNull final String symptomGroupName,
            @NonNull final List<DisplaySymptom> displaySymptoms
    ) {
        mSymptomGroupId = symptomGroupId;
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
        final DisplaySymptomGroup that = (DisplaySymptomGroup) o;
        return mSymptomGroupId.equals(that.mSymptomGroupId);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mSymptomGroupId);
    }

    @Override
    public String toString () {
        return "DisplaySymptomGroup{" +
                "mSymptomGroupId=" + mSymptomGroupId +
                ", mSymptomGroupName='" + mSymptomGroupName + '\'' +
                ", mDisplaySymptoms=" + mDisplaySymptoms +
                ", mSelected=" + mSelected +
                '}';
    }
}
