package org.blagodarie.ui.symptoms;

import android.os.Handler;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;
import androidx.lifecycle.LiveData;

import org.blagodarie.sync.UserSymptomSyncer;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.UserSymptom;

import java.util.Date;
import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplaySymptom
        extends BaseObservable
        implements Comparable<DisplaySymptom> {

    private static final String TAG = DisplaySymptom.class.getSimpleName();

    /**
     * Время подсветки сообщения в миллисекундах. В течении этого времени сообщение нельня еще раз отметить.
     */
    private static final long HIGHLIGHT_TIME = 30000L;

    interface UnconfirmedUserSymptomListener {
        void onConfirm (@NonNull final DisplaySymptom displaySymptom);

        void onCancel (@NonNull final UserSymptom canceledUserSymptom);
    }

    /**
     * Сообщение.
     */
    @NonNull
    private final Symptom mSymptom;

    /**
     * Дата последней отметки.
     */
    @Nullable
    private Date mLastDate;

    /**
     * Количество отметок.
     */
    private long mUserSymptomCount = 0;

    /**
     * Неподтветжденное сообщение.
     */
    @Nullable
    private UserSymptom mUnconfirmedUserSymptom;

    /**
     * Имеются ли несинхронизированные сообщения данного типа.
     */
    private boolean mHaveNotSynced = false;

    /**
     * Подсвечивать ли сообщение.
     */
    private boolean mHighlight = false;

    /**
     * Слушатель подтверждения/отмены сообщения.
     */
    @NonNull
    private final UnconfirmedUserSymptomListener mConfirmUserSymptomListener;

    /**
     * Обработчик подтверждения и подсветки.
     */
    @NonNull
    private Handler mConfirmationHandler = new Handler();

    /**
     * Задача для подтверждения сообщения.
     */
    private final Runnable mConfirmation = this::confirmUnconfirmedUserSymptom;

    /**
     * Задача для отключения подсветки.
     */
    private final Runnable mHighlighting = () -> setHighlight(false);

    public DisplaySymptom (
            @NonNull final Symptom symptom,
            @NonNull final LiveData<Boolean> haveNotSynced,
            @NonNull final LiveData<UserSymptom> notConfirmedUserSymptom,
            @NonNull final UnconfirmedUserSymptomListener unconfirmedUserSymptomListener
    ) {
        Log.d(TAG, "DisplaySymptom");
        mSymptom = symptom;
        haveNotSynced.observeForever(this::setHaveNotSynced);
        notConfirmedUserSymptom.observeForever(latestUserSymptom -> {
            if (latestUserSymptom != null && !latestUserSymptom.equals(mUnconfirmedUserSymptom)) {
                setNotConfirmedUserSymptom(latestUserSymptom);
            }
        });
        mConfirmUserSymptomListener = unconfirmedUserSymptomListener;
    }

    @NonNull
    final Identifier getSymptomId () {
        return mSymptom.getId();
    }

    @NonNull
    @Bindable
    public final String getSymptomName () {
        return mSymptom.getName();
    }

    @Nullable
    @Bindable
    public final Date getLastDate () {
        if (mUnconfirmedUserSymptom != null) {
            return mUnconfirmedUserSymptom.getTimestamp();
        } else {
            return mLastDate;
        }
    }

    final void setLastDate (@Nullable final Date lastDate) {
        mLastDate = lastDate;
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
    }

    @Bindable
    final long getUserSymptomCount () {
        long userSymptomCount = mUserSymptomCount;
        if (mUnconfirmedUserSymptom != null) {
            userSymptomCount++;
        }
        return userSymptomCount;
    }

    final void setUserSymptomCount (final long userSymptomCount) {
        mUserSymptomCount = userSymptomCount;
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
    }

    @Bindable
    public final boolean isHaveNotSynced () {
        return mHaveNotSynced;
    }

    private void setHaveNotSynced (boolean haveNotSynced) {
        mHaveNotSynced = haveNotSynced;
        notifyPropertyChanged(org.blagodarie.BR.haveNotSynced);
    }

    @Bindable
    public final boolean isHighlight () {
        return mHighlight;
    }

    private void setHighlight (boolean highlight) {
        mHighlight = highlight;
        notifyPropertyChanged(org.blagodarie.BR.highlight);
    }

    /**
     * Запускает таймер подтверждения сообщения.
     *
     * @param delay Время таймера.
     */
    private void startConfirmationTimer (final long delay) {
        Log.d(TAG, "startConfirmationTimer");
        mConfirmationHandler.postDelayed(mConfirmation, delay);
    }

    /**
     * Запускает таймер подсветки сообщения.
     */
    private void startHighlightTimer () {
        Log.d(TAG, "startHighlightTimer");
        mConfirmationHandler.postDelayed(mHighlighting, HIGHLIGHT_TIME);
    }

    @Nullable
    @Bindable
    public final UserSymptom getNotConfirmedUserSymptom () {
        return mUnconfirmedUserSymptom;
    }

    /**
     * Очищает неподтвержденный симптом.
     */
    private void clearNotConfirmedUserSymptom () {
        mUnconfirmedUserSymptom = null;
        notifyPropertyChanged(org.blagodarie.BR.notConfirmedUserSymptom);
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
        notifyPropertyChanged(org.blagodarie.BR.userSymptomCount);
    }

    /**
     * Устанавливает неподтвержденное сообщение.
     *
     * @param notConfirmedUserSymptom Неподтвержденное сообщение.
     */
    private void setNotConfirmedUserSymptom (@NonNull final UserSymptom notConfirmedUserSymptom) {
        Log.d(TAG, "setNotConfirmedUserSymptom notConfirmedUserSymptom=" + notConfirmedUserSymptom);
        final long howLongAgo = System.currentTimeMillis() - notConfirmedUserSymptom.getTimestamp().getTime();
        Log.d(TAG, "howLongAgo=" + howLongAgo);
        if (howLongAgo <= UserSymptomSyncer.USER_SYMPTOM_CONFIRMATION_TIME) {
            mUnconfirmedUserSymptom = notConfirmedUserSymptom;
            startConfirmationTimer(UserSymptomSyncer.USER_SYMPTOM_CONFIRMATION_TIME - howLongAgo);
        }
        notifyPropertyChanged(org.blagodarie.BR.notConfirmedUserSymptom);
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
        notifyPropertyChanged(org.blagodarie.BR.userSymptomCount);
    }

    final void highlight () {
        setHighlight(true);
        startHighlightTimer();
    }

    /**
     * Подтверждает неподтвержденное сообщение.
     */
    private void confirmUnconfirmedUserSymptom () {
        Log.d(TAG, "confirmUnconfirmedUserSymptom");
        mConfirmUserSymptomListener.onConfirm(this);
        clearConfirmationTimer();
        clearNotConfirmedUserSymptom();
    }

    /**
     * Отменяет неподтвержденное сообщение.
     */
    public final void cancelUnconfirmedUserSymptom () {
        Log.d(TAG, "cancelUnconfirmedUserSymptom");
        clearConfirmationTimer();

        setHighlight(false);
        clearHighlightTimer();

        if (mUnconfirmedUserSymptom != null) {
            mConfirmUserSymptomListener.onCancel(mUnconfirmedUserSymptom);
        }

        clearNotConfirmedUserSymptom();
    }

    /**
     * Очищает таймер подтверждения.
     */
    private void clearConfirmationTimer () {
        Log.d(TAG, "clearConfirmationTimer");
        mConfirmationHandler.removeCallbacks(mConfirmation);
    }

    /**
     * Очищает таймер подсветки.
     */
    private void clearHighlightTimer () {
        Log.d(TAG, "clearHighlightTimer");
        mConfirmationHandler.removeCallbacks(mHighlighting);
    }

    @Override
    public int compareTo (@NonNull final DisplaySymptom o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.getLastDate() == null ? 0 : this.getLastDate().getTime();
            long otherTimestamp = o.getLastDate() == null ? 0 : o.getLastDate().getTime();
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.getSymptomName().compareTo(o.getSymptomName());
            }
        }
        return result;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplaySymptom that = (DisplaySymptom) o;
        return mUserSymptomCount == that.mUserSymptomCount &&
                mHaveNotSynced == that.mHaveNotSynced &&
                mHighlight == that.mHighlight &&
                mSymptom.equals(that.mSymptom) &&
                Objects.equals(mLastDate, that.mLastDate) &&
                Objects.equals(mUnconfirmedUserSymptom, that.mUnconfirmedUserSymptom);
    }

    @Override
    public int hashCode () {
        return Objects.hash(
                mSymptom,
                mLastDate,
                mUserSymptomCount,
                mUnconfirmedUserSymptom,
                mHaveNotSynced,
                mHighlight
        );
    }

    @Override
    public String toString () {
        return "DisplaySymptom{" +
                "mSymptom=" + mSymptom +
                ", mLastDate=" + mLastDate +
                ", mUserSymptomCount=" + mUserSymptomCount +
                ", mUnconfirmedUserSymptom=" + mUnconfirmedUserSymptom +
                ", mHaveNotSynced=" + mHaveNotSynced +
                ", mHighlight=" + mHighlight +
                ", mConfirmUserSymptomListener=" + mConfirmUserSymptomListener +
                ", mConfirmationHandler=" + mConfirmationHandler +
                ", mConfirmation=" + mConfirmation +
                ", mHighlighting=" + mHighlighting +
                '}';
    }
}
