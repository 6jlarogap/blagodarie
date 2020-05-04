package org.blagodarie;

import org.blagodarie.sync.SyncAdapter;
import org.blagodarie.sync.SyncService;
import org.blagodarie.ui.splash.SplashActivity;
import org.blagodarie.ui.symptoms.SymptomsActivity;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public final class LogReader {

    private LogReader(){}

    public static String getLog(){
        Process logcat;
        final StringBuilder log = new StringBuilder();
        try {
            logcat = Runtime.getRuntime().exec(new String[]{
                    "logcat",
                    "-d",
                    "-s",
                    "-v long",
                    "BlagodarieApp:D",
                    "SplashActivity:D",
                    "AuthenticationActivity:D",
                    "Authenticator:D",
                    "AuthenticatorService:D",
                    "GreetingFragment:D",
                    "SignInFragment:D",
                    "SignUpFragment:D",
                    "StartFragment:D",
                    "SyncService:D",
                    "SyncAdapter:D",
                    "UserSymptomSyncer:D",
                    "SymptomsActivity:D",
                    "MigrationKeeper:D",
            });
            BufferedReader br = new BufferedReader(new InputStreamReader(logcat.getInputStream()), 4 * 1024);
            String line;
            String separator = System.getProperty("line.separator");
            while ((line = br.readLine()) != null) {
                log.append(line);
                log.append(separator);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return log.toString();
    }
}
