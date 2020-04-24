package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.Index;

import java.util.ArrayList;
import java.util.List;

@Entity (
        tableName = "tbl_symptom",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"name"}, unique = true)
        }
)
public final class Symptom
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "name")
    private final String Name;

    Symptom (
            @NonNull final Long Id,
            @NonNull final String Name
    ) {
        super(Id);
        this.Name = Name;
    }

    @Override
    @NonNull
    public Long getId(){
        assert super.getId() != null;
        return super.getId();
    }

    @NonNull
    public String getName () {
        return Name;
    }

    @NonNull
    @Override
    public String toString () {
        return "Symptom{" +
                "Id=" + getId() +
                ", Name='" + Name + '\'' +
                '}';
    }

    public static List<Symptom> getSymptoms () {
        final List<Symptom> symptoms = new ArrayList<>();
        symptoms.add(new Symptom(25L, "Пробуждение"));
        symptoms.add(new Symptom(19L, "Хорошее настроение"));
        symptoms.add(new Symptom(15L, "Хорошее самочувствие"));
        symptoms.add(new Symptom(20L, "Плохое настроение"));
        symptoms.add(new Symptom(29L, "Плохое самочувствие"));
        symptoms.add(new Symptom(1L, "Нехватка питьевой воды"));
        symptoms.add(new Symptom(2L, "Нехватка еды"));
        symptoms.add(new Symptom(3L, "Нехватка лекарств"));
        symptoms.add(new Symptom(17L, "Повышенное давление"));
        symptoms.add(new Symptom(18L, "Пониженное давление"));
        symptoms.add(new Symptom(16L, "Сердечная боль"));
        symptoms.add(new Symptom(11L, "Головная боль"));
        symptoms.add(new Symptom(10L, "Сухость носа"));
        symptoms.add(new Symptom(26L, "Заложенность носа"));
        symptoms.add(new Symptom(27L, "Насморк"));
        symptoms.add(new Symptom(5L, "Температура"));
        symptoms.add(new Symptom(28L, "Озноб"));
        symptoms.add(new Symptom(24L, "Аллергия"));
        symptoms.add(new Symptom(6L, "Кашель"));

        symptoms.add(new Symptom(4L, "Слабость"));
        symptoms.add(new Symptom(7L, "Боль в груди при дыхании"));
        symptoms.add(new Symptom(8L, "Затруднённое дыхание"));
        symptoms.add(new Symptom(9L, "Одышка"));
        symptoms.add(new Symptom(12L, "Боль и ломота в мышцах и суставах"));
        symptoms.add(new Symptom(13L, "Рвота"));
        symptoms.add(new Symptom(14L, "Диарея"));
        symptoms.add(new Symptom(21L, "Зубная боль"));
        symptoms.add(new Symptom(22L, "Боль в ушах"));
        symptoms.add(new Symptom(23L, "Головокружение"));
        symptoms.add(new Symptom(30L, "Чувство тревоги"));
        symptoms.add(new Symptom(31L, "Похолодало"));
        symptoms.add(new Symptom(32L, "Потеплело"));
        symptoms.add(new Symptom(33L, "Дождь"));
        symptoms.add(new Symptom(34L, "Ветер"));
        symptoms.add(new Symptom(35L, "Жара"));
        symptoms.add(new Symptom(36L, "Астма"));
        symptoms.add(new Symptom(37L, "Хорошая погода"));
        symptoms.add(new Symptom(40L, "Влажно"));
        symptoms.add(new Symptom(41L, "Сухо"));
        symptoms.add(new Symptom(42L, "Прохладно"));
        symptoms.add(new Symptom(44L, "Прием пищи"));
        symptoms.add(new Symptom(45L, "Запор"));
        symptoms.add(new Symptom(46L, "Чихание"));
        symptoms.add(new Symptom(47L, "Першит в горле"));
        symptoms.add(new Symptom(48L, "Пасмурно"));
        symptoms.add(new Symptom(49L, "Учащённое сердцебиение"));
        return symptoms;
    }
}
