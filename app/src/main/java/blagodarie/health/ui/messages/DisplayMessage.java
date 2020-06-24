package blagodarie.health.ui.messages;

import android.os.Handler;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;
import androidx.lifecycle.LiveData;

import blagodarie.health.database.Message;
import blagodarie.health.sync.UserMessageSyncer;
import blagodarie.health.database.Identifier;
import blagodarie.health.database.UserMessage;

import java.util.Date;
import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplayMessage
        extends BaseObservable
        implements Comparable<DisplayMessage> {

    private static final String TAG = DisplayMessage.class.getSimpleName();

    /**
     * Время подсветки сообщения в миллисекундах. В течении этого времени сообщение нельня еще раз отметить.
     */
    private static final long HIGHLIGHT_TIME = 30000L;

    interface UnconfirmedUserMessageListener {
        void onConfirm (@NonNull final DisplayMessage displayMessage);

        void onCancel (@NonNull final UserMessage canceledUserMessage);
    }

    /**
     * Сообщение.
     */
    @NonNull
    private final Message mMessage;

    /**
     * Дата последней отметки.
     */
    @Nullable
    private Date mLastDate;

    /**
     * Количество отметок.
     */
    private long mUserMessageCount = 0;

    /**
     * Неподтветжденное сообщение.
     */
    @Nullable
    private UserMessage mUnconfirmedUserMessage;

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
    private final UnconfirmedUserMessageListener mUnconfirmedUserMessageListener;

    /**
     * Обработчик подтверждения и подсветки.
     */
    @NonNull
    private Handler mConfirmationHandler = new Handler();

    /**
     * Задача для подтверждения сообщения.
     */
    private final Runnable mConfirmation = this::confirmUnconfirmedUserMessage;

    /**
     * Задача для отключения подсветки.
     */
    private final Runnable mHighlighting = () -> setHighlight(false);

    public DisplayMessage (
            @NonNull final Message message,
            @NonNull final LiveData<Boolean> haveNotSynced,
            @NonNull final LiveData<UserMessage> notConfirmedUserMessage,
            @NonNull final UnconfirmedUserMessageListener unconfirmedUserMessageListener
    ) {
        Log.d(TAG, "DisplayMessage");
        mMessage = message;
        haveNotSynced.observeForever(this::setHaveNotSynced);
        notConfirmedUserMessage.observeForever(latestUserMessage -> {
            if (latestUserMessage != null && !latestUserMessage.equals(mUnconfirmedUserMessage)) {
                setNotConfirmedUserMessage(latestUserMessage);
            }
        });
        mUnconfirmedUserMessageListener = unconfirmedUserMessageListener;
    }

    @NonNull
    final Identifier getMessageId () {
        return mMessage.getId();
    }

    @NonNull
    @Bindable
    public final String getMessageName () {
        return mMessage.getName();
    }

    @Nullable
    @Bindable
    public final Date getLastDate () {
        if (mUnconfirmedUserMessage != null) {
            return mUnconfirmedUserMessage.getTimestamp();
        } else {
            return mLastDate;
        }
    }

    final void setLastDate (@Nullable final Date lastDate) {
        mLastDate = lastDate;
        notifyPropertyChanged(blagodarie.health.BR.lastDate);
    }

    @Bindable
    final long getUserMessageCount () {
        long userMessageCount = mUserMessageCount;
        if (mUnconfirmedUserMessage != null) {
            userMessageCount++;
        }
        return userMessageCount;
    }

    final void setUserMessageCount (final long userMessageCount) {
        mUserMessageCount = userMessageCount;
        notifyPropertyChanged(blagodarie.health.BR.lastDate);
    }

    @Bindable
    public final boolean isHaveNotSynced () {
        return mHaveNotSynced;
    }

    private void setHaveNotSynced (boolean haveNotSynced) {
        mHaveNotSynced = haveNotSynced;
        notifyPropertyChanged(blagodarie.health.BR.haveNotSynced);
    }

    @Bindable
    public final boolean isHighlight () {
        return mHighlight;
    }

    private void setHighlight (boolean highlight) {
        mHighlight = highlight;
        notifyPropertyChanged(blagodarie.health.BR.highlight);
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
    public final UserMessage getNotConfirmedUserMessage () {
        return mUnconfirmedUserMessage;
    }

    /**
     * Очищает неподтвержденный симптом.
     */
    private void clearNotConfirmedUserMessage () {
        mUnconfirmedUserMessage = null;
        notifyPropertyChanged(blagodarie.health.BR.notConfirmedUserMessage);
        notifyPropertyChanged(blagodarie.health.BR.lastDate);
        notifyPropertyChanged(blagodarie.health.BR.userMessageCount);
    }

    /**
     * Устанавливает неподтвержденное сообщение.
     *
     * @param notConfirmedUserMessage Неподтвержденное сообщение.
     */
    private void setNotConfirmedUserMessage (@NonNull final UserMessage notConfirmedUserMessage) {
        Log.d(TAG, "setNotConfirmedUserMessage notConfirmedUserMessage=" + notConfirmedUserMessage);
        final long howLongAgo = System.currentTimeMillis() - notConfirmedUserMessage.getTimestamp().getTime();
        Log.d(TAG, "howLongAgo=" + howLongAgo);
        if (howLongAgo <= UserMessageSyncer.USER_MESSAGE_CONFIRMATION_TIME) {
            mUnconfirmedUserMessage = notConfirmedUserMessage;
            startConfirmationTimer(UserMessageSyncer.USER_MESSAGE_CONFIRMATION_TIME - howLongAgo);
        }
        notifyPropertyChanged(blagodarie.health.BR.notConfirmedUserMessage);
        notifyPropertyChanged(blagodarie.health.BR.lastDate);
        notifyPropertyChanged(blagodarie.health.BR.userMessageCount);
    }

    final void highlight () {
        setHighlight(true);
        startHighlightTimer();
    }

    /**
     * Подтверждает неподтвержденное сообщение.
     */
    private void confirmUnconfirmedUserMessage () {
        Log.d(TAG, "confirmUnconfirmedUserMessage");
        mUnconfirmedUserMessageListener.onConfirm(this);
        clearConfirmationTimer();
        clearNotConfirmedUserMessage();
    }

    /**
     * Отменяет неподтвержденное сообщение.
     */
    public final void cancelUnconfirmedUserMessage () {
        Log.d(TAG, "cancelUnconfirmedUserMessage");
        clearConfirmationTimer();

        setHighlight(false);
        clearHighlightTimer();

        if (mUnconfirmedUserMessage != null) {
            mUnconfirmedUserMessageListener.onCancel(mUnconfirmedUserMessage);
        }

        clearNotConfirmedUserMessage();
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
    public int compareTo (@NonNull final DisplayMessage o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.getLastDate() == null ? 0 : this.getLastDate().getTime();
            long otherTimestamp = o.getLastDate() == null ? 0 : o.getLastDate().getTime();
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.getMessageName().compareTo(o.getMessageName());
            }
        }
        return result;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplayMessage that = (DisplayMessage) o;
        return mUserMessageCount == that.mUserMessageCount &&
                mHaveNotSynced == that.mHaveNotSynced &&
                mHighlight == that.mHighlight &&
                mMessage.equals(that.mMessage) &&
                Objects.equals(mLastDate, that.mLastDate) &&
                Objects.equals(mUnconfirmedUserMessage, that.mUnconfirmedUserMessage);
    }

    @Override
    public int hashCode () {
        return Objects.hash(
                mMessage,
                mLastDate,
                mUserMessageCount,
                mUnconfirmedUserMessage,
                mHaveNotSynced,
                mHighlight
        );
    }

    @Override
    public String toString () {
        return "DisplayMessage{" +
                "mMessage=" + mMessage +
                ", mLastDate=" + mLastDate +
                ", mUserMessageCount=" + mUserMessageCount +
                ", mUnconfirmedUserMessage=" + mUnconfirmedUserMessage +
                ", mHaveNotSynced=" + mHaveNotSynced +
                ", mHighlight=" + mHighlight +
                ", mUnconfirmedUserMessageListener=" + mUnconfirmedUserMessageListener +
                ", mConfirmationHandler=" + mConfirmationHandler +
                ", mConfirmation=" + mConfirmation +
                ", mHighlighting=" + mHighlighting +
                '}';
    }
}
