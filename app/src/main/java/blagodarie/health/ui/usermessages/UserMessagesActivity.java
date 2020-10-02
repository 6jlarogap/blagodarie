package blagodarie.health.ui.usermessages;

import android.os.Bundle;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;
import androidx.navigation.NavController;
import androidx.navigation.Navigation;

import blagodarie.health.R;
import blagodarie.health.databinding.UserMessagesActivityBinding;

public final class UserMessagesActivity
        extends AppCompatActivity {

    private static final String TAG = UserMessagesActivity.class.getSimpleName();

    private NavController mNavController;

    private UserMessagesActivityBinding mActivityBinding;

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        Log.d(TAG, "onCreate");
        super.onCreate(savedInstanceState);
        mActivityBinding = DataBindingUtil.setContentView(this, R.layout.user_messages_activity);
        mNavController = Navigation.findNavController(this, R.id.nav_host_fragment);
        if (getIntent().getExtras() != null) {
            mNavController.setGraph(R.navigation.user_messages_navigation, getIntent().getExtras());
        }
    }

}
