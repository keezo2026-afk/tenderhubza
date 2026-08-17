package za.co.tenderhub
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.*
import org.junit.*
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.domain.model.*
import za.co.tenderhub.ui.screens.SaveControllerViewModel
@OptIn(ExperimentalCoroutinesApi::class) class SaveControllerViewModelTest{private val dispatcher=StandardTestDispatcher();@Before fun before(){Dispatchers.setMain(dispatcher)};@After fun after(){Dispatchers.resetMain()}
 @Test fun `saved state changes only after confirmed API success`()=runTest{val repo=FakeSaved();val vm=SaveControllerViewModel(repo);vm.toggle("t1");advanceUntilIdle();Assert.assertTrue("t1" in vm.savedIds.value);repo.fail=true;vm.toggle("t1");advanceUntilIdle();Assert.assertTrue("t1" in vm.savedIds.value);Assert.assertTrue(vm.message.value!!.contains("Couldn't"))}
 class FakeSaved:SavedRepository{override val savedIds=MutableStateFlow<Set<String>>(emptySet());override val reminderStates=MutableStateFlow<Map<String,Boolean>>(emptyMap());var fail=false;override fun clear(){savedIds.value=emptySet()};override suspend fun setSaved(id:String,saved:Boolean):ApiResult<Boolean>{if(fail)return ApiResult.Error("offline");savedIds.value=if(saved)savedIds.value+id else savedIds.value-id;return ApiResult.Success(saved)};override suspend fun refreshStates(ids:List<String>)=ApiResult.Success(savedIds.value);override suspend fun setReminders(id:String,enabled:Boolean)=ApiResult.Success(enabled);override suspend fun list(page:Int)=ApiResult.Success(Page<SavedTenderItem>(emptyList(),1,20,0,0));override suspend fun searches(page:Int)=ApiResult.Success(Page<SavedSearch>(emptyList(),1,20,0,0));override suspend fun createSearch(input:SavedSearchInput)=ApiResult.Error("unused");override suspend fun updateSearch(id:String,input:SavedSearchInput)=ApiResult.Error("unused");override suspend fun deleteSearch(id:String)=ApiResult.Error("unused")}
}
