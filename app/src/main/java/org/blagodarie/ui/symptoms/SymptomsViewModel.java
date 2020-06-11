package org.blagodarie.ui.symptoms;

import android.app.Application;
import android.util.Log;

import androidx.annotation.Keep;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.util.Pair;
import androidx.databinding.ObservableBoolean;
import androidx.databinding.ObservableField;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.Repository;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.LastUserSymptom;
import org.blagodatie.database.SymptomGroupWithSymptoms;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.functions.Action;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsViewModel
        extends AndroidViewModel {

    private static final String TAG = SymptomsViewModel.class.getSimpleName();

    @NonNull
    private List<DisplaySymptomGroup> mDisplaySymptomGroups = new ArrayList<>();

    @NonNull
    private List<DisplaySymptom> mDisplaySymptoms = new ArrayList<>();

    @NonNull
    private final Repository mRepository;

    @NonNull
    private final CompositeDisposable mDisposables = new CompositeDisposable();

    @NonNull
    private List<SymptomGroupWithSymptoms> mSymptomCatalog = new ArrayList<>();

    @NonNull
    private final ObservableField<String> mIncognitoPublicKey;

    @NonNull
    private final ObservableBoolean mShowNoServerConnectionErrMsg = new ObservableBoolean(false);

    @Keep
    public SymptomsViewModel (
            @NonNull final Application application,
            @NonNull final String incognitoPublicKey
    ) {
        super(application);

        mIncognitoPublicKey = new ObservableField<>(incognitoPublicKey);

        mRepository = Repository.getInstance(application.getApplicationContext());
    }

    @Override
    protected final void onCleared () {
        Log.d(TAG, "onCleared");
        mDisposables.dispose();
        super.onCleared();
    }

    final void loadLastValues (
            @NonNull final UUID incognitoId,
            @NonNull final Action action
    ) {
        final Collection<DisplaySymptom> allDisplaySymptoms = new ArrayList<>();
        for (DisplaySymptomGroup displaySymptomGroup : mDisplaySymptomGroups) {
            allDisplaySymptoms.addAll(displaySymptomGroup.getDisplaySymptoms());
        }

        mDisposables.add(
                Observable.
                        fromIterable(allDisplaySymptoms).
                        map(displaySymptom -> new Pair<>(displaySymptom, mRepository.getLastUserSymptom(incognitoId, displaySymptom.getSymptomId()))).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                displaySymptomWithLastUserSymptom -> {
                                    final DisplaySymptom displaySymptom = displaySymptomWithLastUserSymptom.first;
                                    final LastUserSymptom lastUserSymptom = displaySymptomWithLastUserSymptom.second;
                                    if (displaySymptom != null && lastUserSymptom != null) {
                                        displaySymptom.setLastDate(lastUserSymptom.getTimestamp());
                                        displaySymptom.setUserSymptomCount(lastUserSymptom.getSymptomsCount());
                                    }
                                },
                                throwable -> {
                                },
                                action)
        );
    }

    @NonNull
    final List<DisplaySymptom> getDisplaySymptoms () {
        return mDisplaySymptoms;
    }

    @NonNull
    final List<DisplaySymptomGroup> getDisplaySymptomGroups () {
        return mDisplaySymptomGroups;
    }

    @Nullable
    final Identifier getSelectedSymptomGroupId () {
        for (DisplaySymptomGroup displaySymptomGroup : mDisplaySymptomGroups) {
            if (displaySymptomGroup.isSelected()) {
                return displaySymptomGroup.getSymptomGroupId();
            }
        }
        return null;
    }

    final void setSelectedDisplaySymptomGroup (@Nullable final DisplaySymptomGroup selectedGroup) {
        for (DisplaySymptomGroup displaySymptomGroup : mDisplaySymptomGroups) {
            displaySymptomGroup.setSelected(displaySymptomGroup.equals(selectedGroup));
        }
    }

    final void setDisplaySymptoms (@NonNull final List<DisplaySymptom> displaySymptoms) {
        mDisplaySymptoms = displaySymptoms;
    }

    final void setDisplaySymptomGroups (@NonNull final List<DisplaySymptomGroup> displaySymptomGroups) {
        mDisplaySymptomGroups = displaySymptomGroups;
    }

    @NonNull
    List<SymptomGroupWithSymptoms> getSymptomCatalog () {
        return mSymptomCatalog;
    }

    final void setSymptomCatalog (@NonNull final List<SymptomGroupWithSymptoms> symptomCatalog) {
        mSymptomCatalog = symptomCatalog;
    }

    final void orderDisplaySymptoms () {
        Collections.sort(
                mDisplaySymptoms,
                (o1, o2) -> {
                    long difference = o2.getUserSymptomCount() - o1.getUserSymptomCount();
                    if (difference < 0) {
                        return -1;
                    } else if (difference > 0) {
                        return 1;
                    } else {
                        return o1.getSymptomName().compareTo(o2.getSymptomName());
                    }
                });
    }

    final void orderDisplaySymptomGroups () {
        Collections.sort(
                mDisplaySymptomGroups,
                (o1, o2) -> {
                    long difference = o2.getUserSymptomCount() - o1.getUserSymptomCount();
                    if (difference < 0) {
                        return -1;
                    } else if (difference > 0) {
                        return 1;
                    } else {
                        return o1.getSymptomGroupName().compareTo(o2.getSymptomGroupName());
                    }
                });
    }

    @NonNull
    public ObservableField<String> getIncognitoPublicKey () {
        return mIncognitoPublicKey;
    }

    @NonNull
    public ObservableBoolean isShowNoServerConnectionErrMsg () {
        return mShowNoServerConnectionErrMsg;
    }

    static final class Factory
            extends ViewModelProvider.AndroidViewModelFactory {

        @NonNull
        private final Application mApplication;

        @NonNull
        private final String mIncognitoPublicKey;

        Factory (
                @NonNull final Application application,
                @NonNull final String incognitoPublicKey
        ) {
            super(application);
            mApplication = application;
            mIncognitoPublicKey = incognitoPublicKey;
        }


        @NonNull
        @Override
        public <T extends ViewModel> T create (@NonNull final Class<T> modelClass) {
            if (AndroidViewModel.class.isAssignableFrom(modelClass)) {
                try {
                    return modelClass.getConstructor(Application.class, String.class).newInstance(mApplication, mIncognitoPublicKey);
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
