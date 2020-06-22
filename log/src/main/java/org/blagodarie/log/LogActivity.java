package org.blagodarie.log;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.Window;
import android.widget.ScrollView;
import android.widget.Toast;

import androidx.databinding.DataBindingUtil;

import org.blagodarie.log.databinding.SendLogBinding;

import java.io.BufferedReader;
import java.io.InputStreamReader;


public final class LogActivity
        extends Activity
        implements UserActionListener {

    private static final String TAG = LogActivity.class.getSimpleName();

    public static final String ACTION_SEND_LOG = "org.blagodarie.SEND_LOG";

    String mLog;

    @Override
    public void onCreate (Bundle savedInstanceState) {
        Log.d(TAG, "onCreate");
        super.onCreate(savedInstanceState);

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        setFinishOnTouchOutside(false);

        mLog = readLog();
        Log.d(TAG, "mLog=" + mLog);

        initBinding();
    }

    private void initBinding () {
        Log.d(TAG, "initBinding");
        final SendLogBinding activityBinding = DataBindingUtil.setContentView(this, R.layout.send_log);
        activityBinding.setLog(mLog);
        activityBinding.setUserActionListener(this);
        activityBinding.svLog.post(() -> activityBinding.svLog.fullScroll(ScrollView.FOCUS_DOWN));
    }

    private static String readLog () {
        Log.d(TAG, "readLog");
        final StringBuilder log = new StringBuilder();
        try {
            final String cmd = "logcat -d -v long";
            final Process logcat = Runtime.getRuntime().exec(cmd);
            final BufferedReader br = new BufferedReader(new InputStreamReader(logcat.getInputStream()), 4 * 1024);
            final String separator = System.getProperty("line.separator");
            String line;
            while ((line = br.readLine()) != null) {
                log.append(line);
                log.append(separator);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return log.toString();
    }

    @Override
    public void onSend () {
        Log.d(TAG, "onSend");
        final Intent intent = new Intent(Intent.ACTION_SENDTO);
        intent.setData(Uri.parse("mailto:"));
        intent.putExtra(Intent.EXTRA_EMAIL, new String[]{"blagodarie.developer@gmail.com"});
        intent.putExtra(Intent.EXTRA_SUBJECT, "Crash report");
        intent.putExtra(Intent.EXTRA_TEXT, mLog);
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivity(intent);
        }
    }

    @Override
    public void onCopy () {
        Log.d(TAG, "onCopy");
        final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        final ClipData clip = ClipData.newPlainText(getString(R.string.txt_log), mLog);
        if (clipboard != null) {
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onClose () {
        Log.d(TAG, "onClose");
        finish();
    }
}
