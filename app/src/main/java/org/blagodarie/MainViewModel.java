package org.blagodarie;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableBoolean;
import androidx.databinding.ObservableField;
import androidx.lifecycle.ViewModel;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;
import java.util.Timer;
import java.util.TimerTask;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainViewModel
        extends ViewModel {

    private static final long CURRENT_DATE_TIME_UPDATE_PERIOD = 1000L;

    @NonNull
    private final ObservableField<String> mCurrentDateTime = new ObservableField<>(getCurrentDateTimeString());

    @NonNull
    private final ObservableField<Double> mCurrentLatitude = new ObservableField<>();

    @NonNull
    private final ObservableField<Double> mCurrentLongitude = new ObservableField<>();

    @NonNull
    private final ObservableBoolean mShowLocationPermissionRationale = new ObservableBoolean(false);

    @NonNull
    private final ObservableBoolean mShowLocationPermissionDeniedExplanation = new ObservableBoolean(false);

    @NonNull
    private final ObservableBoolean mShowLocationProvidersDisabledWarning = new ObservableBoolean(false);

    @NonNull
    private final Timer mCurrentDateTimeUpdateTimer = new Timer();

    {
        mCurrentDateTimeUpdateTimer.schedule(new TimerTask() {
            @Override
            public void run () {
                mCurrentDateTime.set(getCurrentDateTimeString());
            }
        }, 0, CURRENT_DATE_TIME_UPDATE_PERIOD);
    }

    @NonNull
    private final Set<DisplaySymptom> mSymptoms = new HashSet<>();

    {
        for (Symptom symptom : Symptom.getSymptoms()) {
            mSymptoms.add(new DisplaySymptom(symptom.getId(), symptom.getName()));
        }
    }

    public MainViewModel () {
        super();
    }

    @Override
    protected void onCleared () {
        mCurrentDateTimeUpdateTimer.cancel();
        super.onCleared();
    }

    @NonNull
    final Set<DisplaySymptom> getSymptoms () {
        return mSymptoms;
    }

    @NonNull
    public final ObservableField<String> getCurrentDatetime () {
        return mCurrentDateTime;
    }

    @NonNull
    public final ObservableField<Double> getCurrentLatitude () {
        return mCurrentLatitude;
    }

    @NonNull
    public final ObservableField<Double> getCurrentLongitude () {
        return mCurrentLongitude;
    }

    @NonNull
    public final ObservableBoolean isShowLocationPermissionRationale () {
        return mShowLocationPermissionRationale;
    }

    @NonNull
    public final ObservableBoolean isShowLocationPermissionDeniedExplanation () {
        return mShowLocationPermissionDeniedExplanation;
    }

    @NonNull
    public final ObservableBoolean isShowLocationProvidersDisabledWarning () {
        return mShowLocationProvidersDisabledWarning;
    }

    @NonNull
    private static String getCurrentDateTimeString () {
        return SimpleDateFormat.getDateTimeInstance().format(new Date());
    }
}
