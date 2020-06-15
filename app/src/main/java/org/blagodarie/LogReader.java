package org.blagodarie;

import android.os.Build;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public final class LogReader {

    private LogReader () {
    }

    public static String getLog () {
        Process logcat;
        final StringBuilder log = new StringBuilder();
        try {
            final String cmd = "logcat" +
                    " -d" +
                    " -s" +
                    " -v long" +
                    " BlagodarieApp:D" +
                    " SplashActivity:D" +
                    " AuthenticationActivity:D" +
                    " Authenticator:D" +
                    " AuthenticatorService:D" +
                    " GreetingFragment:D" +
                    " SignInFragment:D" +
                    " SignUpFragment:D" +
                    " StartFragment:D" +
                    " SyncService:D" +
                    " SyncAdapter:D" +
                    " UserSymptomSyncer:D" +
                    " SymptomsActivity:D" +
                    " MigrationKeeper:D" +
                    " GreetingActivity:D" +
                    " DisplaySymptom:D" +
                    " SymptomsViewModel:D" +
                    " SendLogActivity:D";
            logcat = Runtime.getRuntime().exec(cmd);
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
