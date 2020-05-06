package org.blagodarie.ui.symptoms;

import android.app.Application;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableBoolean;
import androidx.databinding.ObservableField;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.Repository;
import org.blagodatie.database.LastUserSymptom;
import org.blagodatie.database.Symptom;

import java.lang.reflect.InvocationTargetException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;
import java.util.UUID;

import io.reactivex.Completable;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsViewModel
        extends AndroidViewModel {

    private static final long CURRENT_DATE_TIME_UPDATE_PERIOD = 1000L;

    @NonNull
    private final ObservableField<String> mCurrentDateTime = new ObservableField<>(getCurrentDateTimeString());

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
    private final ObservableBoolean mLocationEnabled;

    @NonNull
    private final List<DisplaySymptom> mDisplaySymptoms = new ArrayList<>();

    @NonNull
    private final Repository mRepository;

    @NonNull
    private final CompositeDisposable mDisposables = new CompositeDisposable();

    @NonNull
    private final LiveData<List<Symptom>> mSymptoms;

    public SymptomsViewModel (
            @NonNull final Application application,
            @NonNull final UUID incognitoId,
            final boolean locationEnabled
    ) {
        super(application);

        mLocationEnabled = new ObservableBoolean(locationEnabled);

        mRepository = new Repository(application.getApplicationContext());

        mSymptoms = mRepository.getSymptoms();

        loadLastValues(incognitoId);
    }

    @Override
    protected void onCleared () {
        mDisposables.dispose();
        mCurrentDateTimeUpdateTimer.cancel();
        super.onCleared();
    }

    final LiveData<List<Symptom>> getSymptoms (){
        return mSymptoms;
    }

    void loadLastValues (
            @NonNull final UUID incognitoId
    ) {
        Completable.
                fromAction(() -> {
                    for (DisplaySymptom displaySymptom : mDisplaySymptoms) {
                        final LastUserSymptom lastUserSymptom = mRepository.getLastUserSymptom(incognitoId, displaySymptom.getSymptomId());
                        if (lastUserSymptom != null) {
                            displaySymptom.setLastDate(lastUserSymptom.getTimestamp());
                            displaySymptom.setUserSymptomCount(lastUserSymptom.getSymptomsCount());
                            if (lastUserSymptom.getLatitude() != null) {
                                displaySymptom.setLastLatitude(lastUserSymptom.getLatitude());
                            }
                            if (lastUserSymptom.getLongitude() != null) {
                                displaySymptom.setLastLongitude(lastUserSymptom.getLongitude());
                            }
                        }
                    }
                }).
                subscribeOn(Schedulers.io()).
                subscribe();
    }

    @NonNull
    final List<DisplaySymptom> getDisplaySymptoms () {
        return mDisplaySymptoms;
    }

    final void setDisplaySymptoms (@NonNull final List<DisplaySymptom> displaySymptoms) {
        mDisplaySymptoms.clear();
        mDisplaySymptoms.addAll(displaySymptoms);
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
    public final ObservableBoolean isLocationEnabled () {
        return mLocationEnabled;
    }

    @NonNull
    private static String getCurrentDateTimeString () {
        return SimpleDateFormat.getDateTimeInstance().format(new Date());
    }

    static final class Factory
            extends ViewModelProvider.AndroidViewModelFactory {

        @NonNull
        private final Application mApplication;

        @NonNull
        private final UUID mIncognitoId;

        private final boolean mLocationEnabled;

        Factory (
                @NonNull final Application application,
                @NonNull final UUID incognitoId,
                final boolean locationEnabled
        ) {
            super(application);
            mApplication = application;
            mIncognitoId = incognitoId;
            mLocationEnabled = locationEnabled;
        }


        @NonNull
        @Override
        public <T extends ViewModel> T create (@NonNull final Class<T> modelClass) {
            if (AndroidViewModel.class.isAssignableFrom(modelClass)) {
                try {
                    return modelClass.getConstructor(Application.class, UUID.class, boolean.class).newInstance(mApplication, mIncognitoId, mLocationEnabled);
                } catch (NoSuchMethodException |
                        IllegalAccessException |
                        InstantiationException |
                        InvocationTargetException e
                ) {
                    throw new RuntimeException("Cannot create an instance of " + modelClass, e);
                }
            }
            return super.create(modelClass);
        }
    }
}
