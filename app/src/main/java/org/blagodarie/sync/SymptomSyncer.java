package org.blagodarie.sync;

import android.content.SharedPreferences;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import org.blagodarie.Repository;
import org.blagodarie.server.ServerApiResponse;
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
            @NonNull final ServerConnector serverConnector,
            @NonNull final Repository repository,
            @NonNull final SharedPreferences sharedPreferences
    ) throws IOException, JSONException {
        Log.d(TAG, "sync");
        final String symptomChecksum = sharedPreferences.getString(PREF_SYMPTOM_CHECKSUM, "");

        final String content = createJsonContent(symptomChecksum);
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
                    //создать SymptomGroup из JSON
                    final JSONArray symptomGroupJSONArray = responseJSON.getJSONArray("symptom_groups");
                    final Collection<SymptomGroup> newSymptomGroups = getSymptomGroupsFromJsonArray(symptomGroupJSONArray);

                    //создать Symptom из JSON
                    final JSONArray symptomJSONArray = responseJSON.getJSONArray("symptoms");
                    final Collection<Symptom> newSymptoms = getSymptomsFromJsonArray(symptomJSONArray);

                    //обновить справочник симптомов
                    repository.updateSymptoms(newSymptomGroups, newSymptoms);

                    //сохранить контрольную сумму
                    final String newChecksum = responseJSON.getString("checksum");
                    sharedPreferences.edit().putString(PREF_SYMPTOM_CHECKSUM, newChecksum).apply();
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
    private Collection<SymptomGroup> getSymptomGroupsFromJsonArray (
            @NonNull final JSONArray symptomGroupJSONArray
    ) throws JSONException {
        final Collection<SymptomGroup> symptomGroups = new HashSet<>();
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
            symptomGroups.add(symptomGroup);
        }
        return symptomGroups;
    }

    @NonNull
    private Collection<Symptom> getSymptomsFromJsonArray (
            @NonNull final JSONArray symptomJSONArray
    ) throws JSONException {
        final Collection<Symptom> symptoms = new HashSet<>();
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
            symptoms.add(symptom);
        }
        return symptoms;
    }
}
