package blagodarie.health.ui.usermessages;

import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.paging.LivePagedListBuilder;
import androidx.paging.PagedList;
import androidx.recyclerview.widget.LinearLayoutManager;

import org.jetbrains.annotations.NotNull;

import java.util.UUID;
import java.util.concurrent.Executors;

import blagodarie.health.databinding.UserMessagesFragmentBinding;
import blagodarie.health.server.ServerConnector;

public final class UserMessagesFragment
        extends Fragment {

    private static final String TAG = UserMessagesFragment.class.getSimpleName();

    private UserMessagesViewModel mViewModel;

    private UserMessagesFragmentBinding mBinding;

    private UserMessagesAdapter mUserMessagesAdapter;

    private UUID mIncognitoPublicKey;

    private long mMessageId;

    @NotNull
    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            @Nullable final ViewGroup container,
            @Nullable final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        initBinding(inflater, container);
        return mBinding.getRoot();
    }

    private void initBinding (
            @NonNull final LayoutInflater inflater,
            @Nullable final ViewGroup container
    ) {
        Log.d(TAG, "initBinding");
        mBinding = UserMessagesFragmentBinding.inflate(inflater, container, false);
    }

    @Override
    public void onActivityCreated (@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);

        initViewModel();
        initOperationsAdapter();
        setupBinding();
    }

    @Override
    public void onViewCreated (
            @NonNull final View view,
            @Nullable final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onViewCreated");
        super.onViewCreated(view, savedInstanceState);

        final UserMessagesFragmentArgs args = UserMessagesFragmentArgs.fromBundle(requireArguments());

        mIncognitoPublicKey = args.getIncognitoPublicKey();
        mMessageId = args.getMessageId();
    }

    @Override
    public void onStart () {
        Log.d(TAG, "onStart");
        super.onStart();
        refreshOperations();
    }

    @Override
    public void onDestroy () {
        Log.d(TAG, "onDestroy");
        super.onDestroy();
        mBinding = null;
    }

    private void initOperationsAdapter () {
        mUserMessagesAdapter = new UserMessagesAdapter();
    }

    private void initViewModel () {
        mViewModel = new ViewModelProvider(requireActivity()).get(UserMessagesViewModel.class);
    }

    private void setupBinding () {
        mBinding.rvUserMessages.setLayoutManager(new LinearLayoutManager(requireContext()));
        mBinding.rvUserMessages.setAdapter(mUserMessagesAdapter);
    }

    private void refreshOperations () {
        final UserMessagesDataSource.OperationsDataSourceFactory sourceFactory = new UserMessagesDataSource.OperationsDataSourceFactory(mIncognitoPublicKey, mMessageId, new ServerConnector(requireContext()));

        final PagedList.Config config = new PagedList.Config.Builder()
                .setEnablePlaceholders(false)
                .setPageSize(10)
                .build();

        mViewModel.setUserMessages(
                new LivePagedListBuilder<>(sourceFactory, config).
                        setFetchExecutor(Executors.newSingleThreadExecutor()).
                        build()
        );
        mViewModel.getUserMessages().observe(requireActivity(), mUserMessagesAdapter::submitList);
    }
}
