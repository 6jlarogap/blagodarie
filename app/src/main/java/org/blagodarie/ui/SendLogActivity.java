package org.blagodarie.ui;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.Window;

import androidx.databinding.DataBindingUtil;

import org.blagodarie.LogReader;
import org.blagodarie.R;
import org.blagodarie.databinding.SendLogBinding;

public class SendLogActivity
        extends Activity
        implements View.OnClickListener {

    String mLog;

    @Override
    public void onCreate (Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE); // make a dialog without a titlebar
        setFinishOnTouchOutside(false); // prevent users from dismissing the dialog by tapping outside
        setContentView(R.layout.send_log);
        SendLogBinding mActivityBinding = DataBindingUtil.setContentView(this, R.layout.send_log);
        mLog = LogReader.getLog();
        mActivityBinding.setLog(mLog);
        findViewById(R.id.btnShare).setOnClickListener(this);
    }


    @Override
    public void onClick (View v) {
        switch (v.getId()){
            case R.id.btnShare:
                sendLog();
                break;
        }
    }

    private void sendLog () {
        Intent intent = new Intent(Intent.ACTION_SENDTO);
        intent.setData(Uri.parse("mailto:")); // only email apps should handle this
        intent.putExtra(Intent.EXTRA_EMAIL, new String[]{"blagodarie.developer@gmail.com"});
        intent.putExtra(Intent.EXTRA_SUBJECT, "Crash report");
        intent.putExtra(Intent.EXTRA_TEXT, mLog);
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivity(intent);
        }
    }
}
