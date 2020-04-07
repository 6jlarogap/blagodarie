package org.blagodarie;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableDouble;
import androidx.databinding.ObservableField;
import androidx.lifecycle.ViewModel;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;
import java.util.Timer;
import java.util.TimerTask;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainViewModel
        extends ViewModel {

    public ObservableDouble mCurrentLatitude = new ObservableDouble();
    public ObservableDouble mCurrentLongitude = new ObservableDouble();
    public ObservableField<String> mCurrentDataTime = new ObservableField<>("");

    @NonNull
    private final Set<DisplaySymptom> mSymptoms = new HashSet<>();

    {
        for (Symptom symptom : Symptom.getSymptoms()) {
            mSymptoms.add(new DisplaySymptom(symptom.getId(), symptom.getName()));
        }
    }

    public MainViewModel () {
        super();
        Timer timer = new Timer();
        timer.schedule(new TimerTask() {
            @Override
            public void run () {
                mCurrentDataTime.set(SimpleDateFormat.getDateTimeInstance().format(new Date()));
            }
        },  0, 1000L);
    }

    final Set<DisplaySymptom> getSymptoms () {
        return mSymptoms;
    }
}
