package org.blagodarie;

import androidx.annotation.NonNull;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class Symptom {

    @NonNull
    private final Long mId;

    @NonNull
    private final String mName;

    @NonNull
    private static final Set<Symptom> SYMPTOMS = new HashSet<>();

    static {
        SYMPTOMS.add(new Symptom(1L, "Жажда"));
        SYMPTOMS.add(new Symptom(2L, "Голод"));
        SYMPTOMS.add(new Symptom(3L, "Нехватка лекарств"));
        SYMPTOMS.add(new Symptom(4L, "Слабость"));
        SYMPTOMS.add(new Symptom(5L, "Температура"));
        SYMPTOMS.add(new Symptom(6L, "Кашель"));
        SYMPTOMS.add(new Symptom(7L, "Боль в груди при дыхании"));
        SYMPTOMS.add(new Symptom(8L, "Затруднённое дыхание"));
        SYMPTOMS.add(new Symptom(9L, "Одышка"));
        SYMPTOMS.add(new Symptom(10L, "Заложенность носа или насморк"));
        SYMPTOMS.add(new Symptom(11L, "Головная боль"));
        SYMPTOMS.add(new Symptom(12L, "Боль и ломота в мышцах и суставах"));
        SYMPTOMS.add(new Symptom(13L, "Рвота"));
        SYMPTOMS.add(new Symptom(14L, "Понос"));
        SYMPTOMS.add(new Symptom(15L, "Хорошее самочувтсвие"));
        SYMPTOMS.add(new Symptom(16L, "Сердечная боль"));
        SYMPTOMS.add(new Symptom(17L, "Гипертония"));
        SYMPTOMS.add(new Symptom(18L, "Гипотония"));
    }

    private Symptom (
            @NonNull final Long id,
            @NonNull final String name
    ) {
        mId = id;
        mName = name;
    }

    @NonNull
    public final Long getId () {
        return mId;
    }

    @NonNull
    public final String getName () {
        return mName;
    }

    @Override
    public final boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        final Symptom symptom = (Symptom) o;
        return mId.equals(symptom.mId);
    }

    @Override
    public final int hashCode () {
        return Objects.hash(mId);
    }

    @Override
    public final String toString () {
        return "Symptom{" +
                "mId=" + mId +
                ", mName='" + mName + '\'' +
                '}';
    }

    static Set<Symptom> getSymptoms () {
        return SYMPTOMS;
    }
}
