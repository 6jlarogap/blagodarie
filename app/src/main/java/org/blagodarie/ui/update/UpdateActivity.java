package org.blagodarie.ui.update;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.FileProvider;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.BuildConfig;
import org.blagodarie.R;
import org.blagodarie.databinding.UpdateActivityBinding;

import java.io.File;

import static org.blagodarie.ui.update.UpdateManager.DownloadStatus.RUN;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class UpdateActivity
        extends AppCompatActivity
        implements UpdateManager.ProgressListener {

    private static final String FILE_BASE_PATH = "file://";
    private static final String PROVIDER_PATH = ".provider";
    private static final String APP_INSTALL_PATH = "\"application/vnd.android.package-archive\"";

    private static final String EXTRA_LATEST_VERSION_NAME = "org.blagodarie.ui.update.LATEST_VERSION_NAME";
    private static final String EXTRA_LATEST_VERSION_URI = "org.blagodarie.ui.update.LATEST_VERSION_URI";

    private UpdateViewModel mViewModel;


    boolean mDownloadInProgress = false;

    private String mLatestVersionName;

    private Uri mLatestVersionUri;

    private String mFileName;

    private File mFile;

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mLatestVersionName = getIntent().getStringExtra(EXTRA_LATEST_VERSION_NAME);
        mLatestVersionUri = getIntent().getParcelableExtra(EXTRA_LATEST_VERSION_URI);
        mFileName = String.format("%s %s.apk", getString(R.string.app_name), mLatestVersionName);
        mFile = new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), mFileName);

        restoreFromBundle(savedInstanceState);


        initViewModel();

        final UpdateActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.update_activity);
        mainActivityBinding.setViewModel(mViewModel);

        UpdateManager.getInstance().setProgressListener(this);

        if (mFile.exists()) {
            if (UpdateManager.getInstance().getDownloadStatus() != RUN) {
                startInstall();
            }
        } else {
            UpdateManager.getInstance().startDownload(
                    getApplicationContext(),
                    mFile,
                    mLatestVersionUri
            );
        }
    }

    private void restoreFromBundle (@Nullable final Bundle savedInstanceState) {
        if (savedInstanceState != null) {
            mDownloadInProgress = savedInstanceState.getBoolean("mDownloadInProgress");
        }
    }

    @Override
    protected void onDestroy () {
        super.onDestroy();
    }

    @Override
    protected void onSaveInstanceState (@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putBoolean("mDownloadInProgress", mDownloadInProgress);
    }

    private void initViewModel () {
        //создаем фабрику
        final UpdateViewModel.Factory factory = new UpdateViewModel.Factory(mLatestVersionName);

        //создаем UpdateViewModel
        mViewModel = new ViewModelProvider(this, factory).get(UpdateViewModel.class);
    }

    private void startInstall () {
        String destination = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS).toString() + "/";
        destination += mFileName;
        Uri uri = Uri.parse(FILE_BASE_PATH + destination);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            Uri contentUri = FileProvider.getUriForFile(
                    this,
                    BuildConfig.APPLICATION_ID + PROVIDER_PATH,
                    new File(destination)
            );
            Intent install = new Intent(Intent.ACTION_VIEW);
            install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            install.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            install.putExtra(Intent.EXTRA_NOT_UNKNOWN_SOURCE, true);
            install.setData(contentUri);
            startActivity(install);
        } else {
            Intent install = new Intent(Intent.ACTION_VIEW);
            install.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            install.setDataAndType(
                    uri,
                    APP_INSTALL_PATH
            );
            startActivity(install);
        }
        finish();
    }

    private void showRepeatDialog () {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.txt_download_failed);
        builder.setMessage(getString(R.string.txt_want_repeat));
        builder.setPositiveButton(R.string.action_repeat, (dialog, which) -> UpdateManager.getInstance().startDownload(
                getApplicationContext(),
                mFile,
                mLatestVersionUri
        ));
        builder.setNegativeButton(R.string.action_finish, (dialog, which) -> finish());
        builder.create();
        builder.show();
    }

    public static Intent createIntent (
            @NonNull final Context context,
            @NonNull final String versionName,
            @NonNull final Uri latestVersionUri
    ) {
        final Intent intent = new Intent(context, UpdateActivity.class);
        intent.putExtra(EXTRA_LATEST_VERSION_NAME, versionName);
        intent.putExtra(EXTRA_LATEST_VERSION_URI, latestVersionUri);
        return intent;
    }

    @Override
    public void onNext (long total, long downloaded) {
        mViewModel.getTotalBytes().set((float) total / 1000000F);
        if (total >= 0) {
            mViewModel.getDownloadedBytes().set((float) downloaded / 1000000F);
            mViewModel.getProgress().set((int) ((downloaded * 100L) / total));
        }
    }

    @Override
    public void onSuccess () {
        mViewModel.getProgress().set(100);
        mViewModel.getDownloadedBytes().set(mViewModel.getTotalBytes().get());
        startInstall();
    }

    @Override
    public void onFail () {
        showRepeatDialog();
    }
}