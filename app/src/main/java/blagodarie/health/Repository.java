package blagodarie.health;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

import blagodarie.health.database.HealthDatabase;
import blagodarie.health.database.Identifier;
import blagodarie.health.database.LastUserMessage;
import blagodarie.health.database.LastUserMessageDao;
import blagodarie.health.database.Message;
import blagodarie.health.database.MessageDao;
import blagodarie.health.database.MessageGroup;
import blagodarie.health.database.MessageGroupDao;
import blagodarie.health.database.MessageGroupWithMessages;
import blagodarie.health.database.UserMessage;
import blagodarie.health.database.UserMessageDao;

public final class Repository {

    private static final String TAG = Repository.class.getSimpleName();

    private static volatile Repository INSTANCE;

    @NonNull
    private final HealthDatabase mHealthDatabase;

    @NonNull
    private final MessageGroupDao mMessageGroupDao;

    @NonNull
    private final MessageDao mMessageDao;

    @NonNull
    private final UserMessageDao mUserMessageDao;

    @NonNull
    private final LastUserMessageDao mLastUserMessageDao;

    private LiveData<List<MessageGroupWithMessages>> mMessageGroupsWithMessages;

    private Repository (@NonNull final Context context) {
        mHealthDatabase = HealthDatabase.getDatabase(context);
        mMessageGroupDao = mHealthDatabase.messageGroupDao();
        mMessageDao = mHealthDatabase.messageDao();
        mUserMessageDao = mHealthDatabase.userMessageDao();
        mLastUserMessageDao = mHealthDatabase.lastUserMessageDao();
    }

    public static Repository getInstance (@NonNull final Context context) {
        if (INSTANCE == null) {
            synchronized (Repository.class) {
                if (INSTANCE == null) {
                    INSTANCE = new Repository(context);
                }
            }
        }
        return INSTANCE;
    }

    public final LiveData<Boolean> isHaveNotSyncedUserMessages (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier messageId
    ) {
        Log.d(TAG, "isHaveNotSyncedUserMessages");
        return mUserMessageDao.isHaveNotSynced(incognitoId, messageId);
    }


    public final LiveData<UserMessage> getLatestUserMessage (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier messageId
    ) {
        Log.d(TAG, "getLatestUserMessage");
        return mUserMessageDao.getLatestUserMessage(incognitoId, messageId);
    }

    public final List<UserMessage> getNotSyncedUserMessages (@NonNull final UUID incognitoId) {
        Log.d(TAG, "getNotSyncedUserMessages");
        return mUserMessageDao.getNotSynced(incognitoId);
    }

    public final void updateLastUserMessage (@NonNull final UserMessage userMessage) {
        Log.d(TAG, "updateLastUserMessage");
        //выполнить в транзакции
        mHealthDatabase.runInTransaction(() -> {
            //получить lastUserMessage, соответствующий userMessage
            LastUserMessage lastUserMessage = mLastUserMessageDao.get(userMessage.getIncognitoId(), userMessage.getMessageId());
            //если существует
            if (lastUserMessage != null) {
                //обновить данные
                lastUserMessage.setTimestamp(userMessage.getTimestamp());
                lastUserMessage.setMessagesCount(lastUserMessage.getMessagesCount() + 1);
                if (userMessage.getLatitude() != null &&
                        userMessage.getLongitude() != null) {
                    lastUserMessage.setLatitude(userMessage.getLatitude());
                    lastUserMessage.setLongitude(userMessage.getLongitude());
                }
                mLastUserMessageDao.update(lastUserMessage);
            } else {
                //иначе создать новый lastUserMessage
                lastUserMessage = new LastUserMessage(
                        userMessage.getIncognitoId(),
                        userMessage.getMessageId(),
                        userMessage.getTimestamp(),
                        userMessage.getLatitude(),
                        userMessage.getLongitude()
                );
                mLastUserMessageDao.insert(lastUserMessage);
            }
        });
    }

    public final void deleteUserMessage (@NonNull final UserMessage userMessage) {
        Log.d(TAG, "deleteUserMessage");
        mUserMessageDao.delete(userMessage);
    }

    public final void insertUserMessageAndSetId (@NonNull final UserMessage userMessage) {
        Log.d(TAG, "insertUserMessageAndSetId");
        mUserMessageDao.insertAndSetId(userMessage);
    }

    public final LastUserMessage getLastUserMessage (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier messageId
    ) {
        Log.d(TAG, "getLastUserMessage");
        return mLastUserMessageDao.get(incognitoId, messageId);
    }

    public final void deleteUserMessages (@NonNull final Collection<UserMessage> userMessages) {
        Log.d(TAG, "deleteUserMessages");
        mUserMessageDao.delete(userMessages);
    }

    public final void updateMessages (
            @NonNull final Collection<MessageGroup> newMessageGroups,
            @NonNull final Collection<Message> newMessages
    ) {
        Log.d(TAG, "updateMessages");
        mHealthDatabase.runInTransaction(() -> {
            mHealthDatabase.deferForeignKeys();
            //удалить все симптомы
            mMessageDao.deleteAll();
            //удалить все группы симптомов
            mMessageGroupDao.deleteAll();
            //вставить новые группы
            mMessageGroupDao.insert(newMessageGroups);
            //вставить новые симптомы
            mMessageDao.insert(newMessages);
        });
    }

    public final LiveData<List<MessageGroupWithMessages>> getMessageGroupsWithMessages () {
        Log.d(TAG, "getMessageGroupsWithMessages");
        if (mMessageGroupsWithMessages == null) {
            mMessageGroupsWithMessages = mMessageGroupDao.getMessageCatalog();
        }
        return mMessageGroupsWithMessages;
    }

}
