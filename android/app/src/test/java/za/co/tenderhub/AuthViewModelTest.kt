package za.co.tenderhub
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.*
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.domain.model.User
import za.co.tenderhub.ui.navigation.*
@OptIn(ExperimentalCoroutinesApi::class) class AuthViewModelTest{
 private val dispatcher=StandardTestDispatcher();@Before fun before(){Dispatchers.setMain(dispatcher)};@After fun after(){Dispatchers.resetMain()}
 @Test fun `failed restore produces anonymous state`()=runTest{val vm=AuthViewModel(FakeRepo());advanceUntilIdle();Assert.assertEquals(AuthState.Anonymous,vm.state.value)}
 @Test fun `api errors are exposed to UI`()=runTest{val vm=AuthViewModel(FakeRepo());advanceUntilIdle();vm.login("x","y");advanceUntilIdle();Assert.assertTrue(vm.state.value is AuthState.Error)}
 class FakeRepo:AuthRepository{override suspend fun restore()=ApiResult.Error("No session",401);override suspend fun login(email:String,password:String)=ApiResult.Error("API error",500);override suspend fun register(email:String,password:String,first:String,last:String)=ApiResult.Error("API error");override suspend fun logout(){}}
}
