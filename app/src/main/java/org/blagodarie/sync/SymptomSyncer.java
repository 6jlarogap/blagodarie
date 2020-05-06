package org.blagodarie.sync;

import android.content.SharedPreferences;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import org.blagodarie.Repository;
import org.blagodarie.server.ServerConnector;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.SymptomGroup;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Collection;
import java.util.HashSet;

import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

final class SymptomSyncer {

    private static final String TAG = SymptomSyncer.class.getSimpleName();

    private static final String PREF_SYMPTOM_CHECKSUM = "symptomChecksum";

    private static volatile SymptomSyncer INSTANCE;

    private SymptomSyncer () {
    }

    @NonNull
    static SymptomSyncer getInstance () {
        Log.d(TAG, "getInstance");
        synchronized (SymptomSyncer.class) {
            if (INSTANCE == null) {
                INSTANCE = new SymptomSyncer();
            }
        }
        return INSTANCE;
    }


    final synchronized void sync (
            @NonNull final String apiBaseUrl,
            @NonNull final Repository repository,
            @NonNull final SharedPreferences sharedPreferences
    ) throws IOException, JSONException {
        Log.d(TAG, "sync");
        String symptomChecksum = sharedPreferences.getString(PREF_SYMPTOM_CHECKSUM, "");
        if (symptomChecksum == null) {
            symptomChecksum = "";
        }

        final String content = createJsonContent(symptomChecksum);
        Log.d(TAG, "content=" + content);

        final Request request = createRequest(apiBaseUrl, content);
        Log.d(TAG, "request=" + request);

        final Response response = ServerConnector.sendRequestAndGetRespone(request);
        Log.d(TAG, "response.code=" + response.code());

        if (response.code() == 200) {
            if (response.body() != null) {
                final String responseBody = response.body().string();
                Log.d(TAG, "responseBody=" + responseBody);
                final JSONObject responseJSON = new JSONObject(responseBody);
                final boolean changed = responseJSON.getBoolean("changed");
                if (changed) {
                    final JSONArray symptomGroupJSONArray = responseJSON.getJSONArray("symptom_groups");
                    final Collection<SymptomGroup> newSymptomGroups = new HashSet<>();
                    for (int i = 0; i < symptomGroupJSONArray.length(); i++) {
                        final JSONObject symptomGroupJSONObject = symptomGroupJSONArray.getJSONObject(i);
                        final long id = symptomGroupJSONObject.getLong("id");
                        final String name = symptomGroupJSONObject.getString("name");
                        final Long parentId = getNullableLong(symptomGroupJSONObject, "parent_id");
                        final SymptomGroup symptomGroup =
                                new SymptomGroup(
                                        Identifier.newInstance(id),
                                        name,
                                        Identifier.newInstance(parentId)
                                );
                        newSymptomGroups.add(symptomGroup);
                    }

                    final JSONArray symptomJSONArray = responseJSON.getJSONArray("symptoms");
                    final Collection<Symptom> newSymptoms = new HashSet<>();
                    for (int i = 0; i < symptomJSONArray.length(); i++) {
                        final JSONObject symptomJSONObject = symptomJSONArray.getJSONObject(i);
                        final long id = symptomJSONObject.getLong("id");
                        final String name = symptomJSONObject.getString("name");
                        final Long groupId = getNullableLong(symptomJSONObject, "group_id");
                        final Integer order = getNullableInt(symptomJSONObject, "order");
                        final Symptom symptom =
                                new Symptom(
                                        Identifier.newInstance(id),
                                        name,
                                        Identifier.newInstance(groupId),
                                        order
                                );
                        newSymptoms.add(symptom);
                    }
                    repository.updateSymptoms(newSymptomGroups, newSymptoms);
                    final String newChecksum = responseJSON.getString("checksum");
                    sharedPreferences.edit().putString(PREF_SYMPTOM_CHECKSUM, newChecksum).apply();
                }
            }
        }
    }

    private Request createRequest (
            @NonNull final String apiBaseUrl,
            @NonNull final String content
    ) {
        final RequestBody body = RequestBody.create(JSON_TYPE, content);
        return new Request.Builder().
                url(apiBaseUrl + "getsymptoms").
                post(body).
                build();
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
}
