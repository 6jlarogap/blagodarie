package blagodarie.health.sync;

import android.content.SharedPreferences;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import blagodarie.health.Repository;
import blagodarie.health.database.Message;
import blagodarie.health.database.MessageGroup;
import blagodarie.health.server.ServerApiResponse;
import blagodarie.health.server.ServerConnector;
import blagodarie.health.database.Identifier;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Collection;
import java.util.HashSet;

final class MessageSyncer {

    private static final String TAG = MessageSyncer.class.getSimpleName();

    private static final String PREF_MESSAGE_CHECKSUM = "messageChecksum";

    private static volatile MessageSyncer INSTANCE;

    private MessageSyncer () {
    }

    @NonNull
    static MessageSyncer getInstance () {
        Log.d(TAG, "getInstance");
        synchronized (MessageSyncer.class) {
            if (INSTANCE == null) {
                INSTANCE = new MessageSyncer();
            }
        }
        return INSTANCE;
    }


    final synchronized void sync (
            @NonNull final ServerConnector serverConnector,
            @NonNull final Repository repository,
            @NonNull final SharedPreferences sharedPreferences
    ) throws IOException, JSONException {
        Log.d(TAG, "sync");
        String messageChecksum = sharedPreferences.getString(PREF_MESSAGE_CHECKSUM, "");

        if (messageChecksum == null) {
            messageChecksum = "";
        }

        final String content = createJsonContent(messageChecksum);
        Log.d(TAG, "content=" + content);

        final ServerApiResponse serverApiResponse = serverConnector.sendRequestAndGetResponse("getsymptoms", content);
        Log.d(TAG, "serverApiResponse=" + serverApiResponse);

        if (serverApiResponse.getCode() == 200) {
            if (serverApiResponse.getBody() != null) {
                final String responseBody = serverApiResponse.getBody();
                Log.d(TAG, "responseBody=" + responseBody);
                final JSONObject responseJSON = new JSONObject(responseBody);
                final boolean changed = responseJSON.getBoolean("changed");
                //если есть изменения
                if (changed) {
                    //создать MessageGroup из JSON
                    final JSONArray messageGroupJSONArray = responseJSON.getJSONArray("symptom_groups");
                    final Collection<MessageGroup> newMessageGroups = getMessageGroupsFromJsonArray(messageGroupJSONArray);

                    //создать Message из JSON
                    final JSONArray messageJSONArray = responseJSON.getJSONArray("symptoms");
                    final Collection<Message> newMessages = getMessagesFromJsonArray(messageJSONArray);

                    //обновить справочник симптомов
                    repository.updateMessages(newMessageGroups, newMessages);

                    //сохранить контрольную сумму
                    final String newChecksum = responseJSON.getString("checksum");
                    sharedPreferences.edit().putString(PREF_MESSAGE_CHECKSUM, newChecksum).apply();
                }
            }
        }
    }

    private String createJsonContent (
            @NonNull final String checksum
    ) {
        return String.format("{\"checksum\":\"%s\"}", checksum);
    }

    @Nullable
    private Long getNullableLong (
            @NonNull final JSONObject jsonObject,
            @NonNull final String name
    ) throws JSONException {
        if (!jsonObject.isNull(name)) {
            return jsonObject.getLong(name);
        } else {
            return null;
        }
    }

    @Nullable
    private Integer getNullableInt (
            @NonNull final JSONObject jsonObject,
            @NonNull final String name
    ) throws JSONException {
        if (!jsonObject.isNull(name)) {
            return jsonObject.getInt(name);
        } else {
            return null;
        }
    }

    @NonNull
    private Collection<MessageGroup> getMessageGroupsFromJsonArray (
            @NonNull final JSONArray messageGroupJSONArray
    ) throws JSONException {
        final Collection<MessageGroup> messageGroups = new HashSet<>();
        for (int i = 0; i < messageGroupJSONArray.length(); i++) {
            final JSONObject messageGroupJSONObject = messageGroupJSONArray.getJSONObject(i);
            final long id = messageGroupJSONObject.getLong("id");
            final String name = messageGroupJSONObject.getString("name");
            final Long parentId = getNullableLong(messageGroupJSONObject, "parent_id");
            final MessageGroup messageGroup =
                    new MessageGroup(
                            Identifier.newInstance(id),
                            name,
                            Identifier.newInstance(parentId)
                    );
            messageGroups.add(messageGroup);
        }
        return messageGroups;
    }

    @NonNull
    private Collection<Message> getMessagesFromJsonArray (
            @NonNull final JSONArray messageJSONArray
    ) throws JSONException {
        final Collection<Message> messages = new HashSet<>();
        for (int i = 0; i < messageJSONArray.length(); i++) {
            final JSONObject messageJSONObject = messageJSONArray.getJSONObject(i);
            final long id = messageJSONObject.getLong("id");
            final String name = messageJSONObject.getString("name");
            final Long groupId = getNullableLong(messageJSONObject, "group_id");
            final Integer order = getNullableInt(messageJSONObject, "order");
            final Message message =
                    new Message(
                            Identifier.newInstance(id),
                            name,
                            Identifier.newInstance(groupId),
                            order
                    );
            messages.add(message);
        }
        return messages;
    }
}
