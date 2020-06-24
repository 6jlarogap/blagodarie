package blagodarie.health.ui.symptoms;

import androidx.annotation.NonNull;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;

import blagodarie.health.database.Identifier;

import java.util.List;

public final class DisplaySymptomGroup
        extends BaseObservable {

    @NonNull
    private final Identifier mSymptomGroupId;

    @NonNull
    private final String mSymptomGroupName;

    @NonNull
    private final List<DisplaySymptom> mDisplaySymptoms;

    private boolean mSelected = false;

    DisplaySymptomGroup (
            @NonNull final Identifier symptomGroupId,
            @NonNull final String symptomGroupName,
            @NonNull final List<DisplaySymptom> displaySymptoms
    ) {
        mSymptomGroupId = symptomGroupId;
        mSymptomGroupName = symptomGroupName;
        mDisplaySymptoms = displaySymptoms;
    }

    @NonNull
    Identifier getSymptomGroupId () {
        return mSymptomGroupId;
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
        notifyPropertyChanged(blagodarie.health.BR.selected);
    }

    long getUserSymptomCount () {
        long userSymptomCount = 0;
        for (DisplaySymptom displaySymptom : mDisplaySymptoms) {
            userSymptomCount += displaySymptom.getUserSymptomCount();
        }
        return userSymptomCount;
    }

    @Override
    public String toString () {
        return "DisplaySymptomGroup{" +
                ", mSymptomGroupId=" + mSymptomGroupId +
                ", mSymptomGroupName='" + mSymptomGroupName + '\'' +
                ", mSelected=" + mSelected +
                ", mDisplaySymptoms=" + mDisplaySymptoms +
                '}';
    }
}
