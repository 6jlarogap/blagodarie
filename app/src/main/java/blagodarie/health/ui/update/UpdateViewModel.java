package blagodarie.health.ui.update;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableFloat;
import androidx.databinding.ObservableInt;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import java.lang.reflect.InvocationTargetException;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class UpdateViewModel
        extends ViewModel{

    /**
     * Имя последней версии приложения.
     */
    @NonNull
    private final String mVersionName;

    /**
     * Прогресс загрузки в процентах.
     */
    @NonNull
    private final ObservableInt mProgress = new ObservableInt(0);

    /**
     * Всего нужно загрузить МБайт.
     */
    @NonNull
    private final ObservableFloat mTotalBytes = new ObservableFloat(0);

    /**
     * Загружено МБайт.
     */
    @NonNull
    private final ObservableFloat mDownloadedBytes = new ObservableFloat(0);

    public UpdateViewModel (
            @NonNull final String versionName
    ) {
        mVersionName = versionName;
    }

    @NonNull
    public String getVersionName () {
        return mVersionName;
    }

    @NonNull
    public ObservableInt getProgress () {
        return mProgress;
    }

    @NonNull
    public ObservableFloat getTotalBytes () {
        return mTotalBytes;
    }

    @NonNull
    public ObservableFloat getDownloadedBytes () {
        return mDownloadedBytes;
    }

    static final class Factory
            implements ViewModelProvider.Factory {

        @NonNull
        private final String mVersionName;

        Factory (
                @NonNull final String versionName
        ) {
            mVersionName = versionName;
        }

        @NonNull
        @Override
        public <T extends ViewModel> T create (@NonNull final Class<T> modelClass) {
            if (modelClass.isAssignableFrom(UpdateViewModel.class)) {
                try {
                    return modelClass.getConstructor(String.class).newInstance(mVersionName);
                } catch (IllegalAccessException | InstantiationException | InvocationTargetException | NoSuchMethodException e) {
                    e.printStackTrace();
                }
            }
            throw new IllegalArgumentException("Unknown ViewModel class");
        }
    }
}
