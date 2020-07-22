package blagodarie.health.ui.messages;

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

import blagodarie.health.Repository;
import blagodarie.health.database.Identifier;
import blagodarie.health.database.LastUserMessage;
import blagodarie.health.database.MessageGroupWithMessages;

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
public final class MessagesViewModel
        extends AndroidViewModel {

    private static final String TAG = MessagesViewModel.class.getSimpleName();

    @NonNull
    private List<DisplayMessageGroup> mDisplayMessageGroups = new ArrayList<>();

    @NonNull
    private List<DisplayMessage> mDisplayMessages = new ArrayList<>();

    @NonNull
    private final Repository mRepository;

    @NonNull
    private final CompositeDisposable mDisposables = new CompositeDisposable();

    @NonNull
    private List<MessageGroupWithMessages> mMessageCatalog = new ArrayList<>();

    @NonNull
    private final ObservableField<String> mIncognitoPublicKey;

    @NonNull
    private final ObservableBoolean mShowNoServerConnectionErrMsg = new ObservableBoolean(false);

    @Keep
    public MessagesViewModel (
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
        final Collection<DisplayMessage> allDisplayMessages = new ArrayList<>();
        for (DisplayMessageGroup displayMessageGroup : mDisplayMessageGroups) {
            allDisplayMessages.addAll(displayMessageGroup.getDisplayMessages());
        }

        mDisposables.add(
                Observable.
                        fromIterable(allDisplayMessages).
                        map(displayMessage -> new Pair<>(displayMessage, mRepository.getLastUserMessage(incognitoId, displayMessage.getMessageId()))).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                displayMessageWithLastUserMessage -> {
                                    final DisplayMessage displayMessage = displayMessageWithLastUserMessage.first;
                                    final LastUserMessage lastUserMessage = displayMessageWithLastUserMessage.second;
                                    if (displayMessage != null && lastUserMessage != null) {
                                        displayMessage.setLastDate(lastUserMessage.getTimestamp());
                                        displayMessage.setUserMessageCount(lastUserMessage.getMessagesCount());
                                    }
                                },
                                throwable -> {
                                },
                                action)
        );
    }

    @NonNull
    final List<DisplayMessage> getDisplayMessages () {
        return mDisplayMessages;
    }

    @NonNull
    final List<DisplayMessageGroup> getDisplayMessageGroups () {
        return mDisplayMessageGroups;
    }

    @Nullable
    final Identifier getSelectedMessageGroupId () {
        for (DisplayMessageGroup displayMessageGroup : mDisplayMessageGroups) {
            if (displayMessageGroup.isSelected()) {
                return displayMessageGroup.getMessageGroupId();
            }
        }
        return null;
    }

    final void setSelectedDisplayMessageGroup (@Nullable final DisplayMessageGroup selectedGroup) {
        for (DisplayMessageGroup displayMessageGroup : mDisplayMessageGroups) {
            displayMessageGroup.setSelected(displayMessageGroup.equals(selectedGroup));
        }
    }

    final void setDisplayMessages (@NonNull final List<DisplayMessage> displayMessages) {
        mDisplayMessages = displayMessages;
    }

    final void setDisplayMessageGroups (@NonNull final List<DisplayMessageGroup> displayMessageGroups) {
        mDisplayMessageGroups = displayMessageGroups;
    }

    @NonNull
    List<MessageGroupWithMessages> getMessageCatalog () {
        return mMessageCatalog;
    }

    final void setMessageCatalog (@NonNull final List<MessageGroupWithMessages> messageCatalog) {
        mMessageCatalog = messageCatalog;
    }

    final void orderDisplayMessages () {
        Collections.sort(
                mDisplayMessages,
                (o1, o2) -> {
                    long difference = o2.getUserMessageCount() - o1.getUserMessageCount();
                    if (difference < 0) {
                        return -1;
                    } else if (difference > 0) {
                        return 1;
                    } else {
                        return o1.getMessageName().compareTo(o2.getMessageName());
                    }
                });
    }

    final void orderDisplayMessageGroups () {
        Collections.sort(
                mDisplayMessageGroups,
                (o1, o2) -> {
                    long difference = o2.getUserMessageCount() - o1.getUserMessageCount();
                    if (difference < 0) {
                        return -1;
                    } else if (difference > 0) {
                        return 1;
                    } else {
                        return o1.getMessageGroupName().compareTo(o2.getMessageGroupName());
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
