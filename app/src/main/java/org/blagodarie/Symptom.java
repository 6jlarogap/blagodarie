package org.blagodarie;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

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
    private static final List<Symptom> SYMPTOMS = new ArrayList<>();

    static {
        SYMPTOMS.add(new Symptom(25L, "Пробуждение"));
        SYMPTOMS.add(new Symptom(19L, "Хорошее настроение"));
        SYMPTOMS.add(new Symptom(15L, "Хорошее самочувствие"));
        SYMPTOMS.add(new Symptom(20L, "Плохое настроение"));
        SYMPTOMS.add(new Symptom(29L, "Плохое самочувствие"));
        SYMPTOMS.add(new Symptom(1L, "Нехватка питьевой воды"));
        SYMPTOMS.add(new Symptom(2L, "Нехватка еды"));
        SYMPTOMS.add(new Symptom(3L, "Нехватка лекарств"));
        SYMPTOMS.add(new Symptom(17L, "Повышенное давление"));
        SYMPTOMS.add(new Symptom(18L, "Пониженное давление"));
        SYMPTOMS.add(new Symptom(16L, "Сердечная боль"));
        SYMPTOMS.add(new Symptom(11L, "Головная боль"));
        SYMPTOMS.add(new Symptom(10L, "Сухость носа"));
        SYMPTOMS.add(new Symptom(26L, "Заложенность носа"));
        SYMPTOMS.add(new Symptom(27L, "Насморк"));
        SYMPTOMS.add(new Symptom(5L, "Температура"));
        SYMPTOMS.add(new Symptom(28L, "Озноб"));
        SYMPTOMS.add(new Symptom(24L, "Аллергия"));
        SYMPTOMS.add(new Symptom(6L, "Кашель"));

        SYMPTOMS.add(new Symptom(4L, "Слабость"));
        SYMPTOMS.add(new Symptom(7L, "Боль в груди при дыхании"));
        SYMPTOMS.add(new Symptom(8L, "Затруднённое дыхание"));
        SYMPTOMS.add(new Symptom(9L, "Одышка"));
        SYMPTOMS.add(new Symptom(12L, "Боль и ломота в мышцах и суставах"));
        SYMPTOMS.add(new Symptom(13L, "Рвота"));
        SYMPTOMS.add(new Symptom(14L, "Диарея"));
        SYMPTOMS.add(new Symptom(21L, "Зубная боль"));
        SYMPTOMS.add(new Symptom(22L, "Боль в ушах"));
        SYMPTOMS.add(new Symptom(23L, "Головокружение"));
        SYMPTOMS.add(new Symptom(30L, "Чувство тревоги"));
        SYMPTOMS.add(new Symptom(31L, "Похолодало"));
        SYMPTOMS.add(new Symptom(32L, "Потеплело"));
        SYMPTOMS.add(new Symptom(33L, "Дождь"));
        SYMPTOMS.add(new Symptom(34L, "Ветер"));
        SYMPTOMS.add(new Symptom(35L, "Жара"));

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

    public static List<Symptom> getSymptoms () {
        return SYMPTOMS;
    }
}
