package org.blagodarie.ui.log;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.widget.Toast;

import androidx.databinding.DataBindingUtil;

import org.blagodarie.LogReader;
import org.blagodarie.R;
import org.blagodarie.databinding.SendLogBinding;

public class SendLogActivity
        extends Activity
        implements UserActionListener {

    String mLog;

    @Override
    public void onCreate (Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        setFinishOnTouchOutside(false);
        SendLogBinding activityBinding = DataBindingUtil.setContentView(this, R.layout.send_log);
        mLog = LogReader.getLog();
        activityBinding.setLog(mLog);
        activityBinding.setUserActionListener(this);
    }

    @Override
    public void onSend () {
        Intent intent = new Intent(Intent.ACTION_SENDTO);
        intent.setData(Uri.parse("mailto:")); // only email apps should handle this
        intent.putExtra(Intent.EXTRA_EMAIL, new String[]{"blagodarie.developer@gmail.com"});
        intent.putExtra(Intent.EXTRA_SUBJECT, "Crash report");
        intent.putExtra(Intent.EXTRA_TEXT, mLog);
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivity(intent);
        }
    }

    @Override
    public void onCopy () {
        final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        final ClipData clip = ClipData.newPlainText(getString(R.string.txt_log), mLog);
        clipboard.setPrimaryClip(clip);
        Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onClose () {
        finish();
    }
}
