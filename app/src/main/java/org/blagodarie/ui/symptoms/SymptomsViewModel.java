package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableBoolean;
import androidx.databinding.ObservableField;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.Symptom;
import org.blagodarie.db.UserSymptom;
import org.blagodarie.db.UserSymptomDao;

import java.lang.reflect.InvocationTargetException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import io.reactivex.Completable;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsViewModel
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
    private final List<DisplaySymptom> mDisplaySymptoms = new ArrayList<>();

    {
        for (Symptom symptom : Symptom.getSymptoms()) {
            mDisplaySymptoms.add(new DisplaySymptom(symptom.getId(), symptom.getName()));
        }
    }

    public SymptomsViewModel (
            @NonNull final UserSymptomDao userSymptomDao
    ) {
        super();
        loadLastValues(userSymptomDao);
    }

    private void loadLastValues (
            @NonNull final UserSymptomDao userSymptomDao
    ) {
        Completable.
                fromAction(() -> {
                    for (DisplaySymptom displaySymptom : mDisplaySymptoms) {
                        final UserSymptom lastUserSymptom = userSymptomDao.getLastForSymptomId(displaySymptom.getSymptomId());
                        if (lastUserSymptom != null) {
                            displaySymptom.getLastDate().set(new Date(lastUserSymptom.getTimestamp()));
                            if (lastUserSymptom.getLatitude() != null) {
                                displaySymptom.getLastLatitude().set(lastUserSymptom.getLatitude());
                            }
                            if (lastUserSymptom.getLongitude() != null) {
                                displaySymptom.getLastLongitude().set(lastUserSymptom.getLongitude());
                            }
                        }
                    }
                }).
                subscribeOn(Schedulers.io()).
                subscribe();
    }

    @Override
    protected void onCleared () {
        mCurrentDateTimeUpdateTimer.cancel();
        super.onCleared();
    }

    @NonNull
    final List<DisplaySymptom> getDisplaySymptoms () {
        return mDisplaySymptoms;
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

    static final class Factory
            implements ViewModelProvider.Factory {

        @NonNull
        private final UserSymptomDao mUserSymptomDao;

        Factory (
                @NonNull final UserSymptomDao userSymptomDao
        ) {
            mUserSymptomDao = userSymptomDao;
        }

        @NonNull
        @Override
        public <T extends ViewModel> T create (@NonNull final Class<T> modelClass) {
            if (modelClass.isAssignableFrom(SymptomsViewModel.class)) {
                try {
                    return modelClass.getConstructor(UserSymptomDao.class).newInstance(mUserSymptomDao);
                } catch (IllegalAccessException | InstantiationException | InvocationTargetException | NoSuchMethodException e) {
                    e.printStackTrace();
                }
            }
            throw new IllegalArgumentException("Unknown ViewModel class");
        }
    }
}
