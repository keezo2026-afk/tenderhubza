package za.co.tenderhub
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import za.co.tenderhub.ui.navigation.*
import za.co.tenderhub.ui.theme.TenderHubTheme
class MainActivity:ComponentActivity(){override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent{TenderHubTheme{val app=(application as TenderHubApplication);val vm:AuthViewModel=viewModel(factory=object:androidx.lifecycle.ViewModelProvider.Factory{override fun <T:androidx.lifecycle.ViewModel> create(modelClass:Class<T>):T{@Suppress("UNCHECKED_CAST") return AuthViewModel(app.authRepository) as T}});AppNavigation(vm,app.authRepository,app.tenderRepository)}}}}
