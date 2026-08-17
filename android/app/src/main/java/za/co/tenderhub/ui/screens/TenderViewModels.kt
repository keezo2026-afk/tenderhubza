package za.co.tenderhub.ui.screens
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.domain.model.*
sealed interface DataState<out T>{data object Loading:DataState<Nothing>;data class Success<T>(val data:T):DataState<T>;data object Empty:DataState<Nothing>;data class Error(val message:String):DataState<Nothing>}
class HomeViewModel(private val repo:TenderRepository):ViewModel(){private val _state=MutableStateFlow<DataState<HomeResponse>>(DataState.Loading);val state:StateFlow<DataState<HomeResponse>> =_state;init{load()};fun load()=viewModelScope.launch{_state.value=DataState.Loading;_state.value=when(val r=repo.home()){is ApiResult.Success->if(r.value.latest.isEmpty()&&r.value.closing_soon.isEmpty())DataState.Empty else DataState.Success(r.value);is ApiResult.Error->DataState.Error(r.message)}}}
data class SearchResults(val items:List<Tender>,val page:Int,val totalPages:Int,val loadingMore:Boolean=false,val savedAt:Map<String,String> = emptyMap())
data class GeographyOptions(val provinces:List<Province> = emptyList(),val districts:List<District> = emptyList(),val municipalities:List<Municipality> = emptyList())
class SearchViewModel(private val repo:TenderRepository,private val history:SearchHistoryStore):ViewModel(){
 val historyItems=history.items;fun clearHistory()=history.clear();fun removeHistory(value:String)=history.remove(value)
 private val _state=MutableStateFlow<DataState<SearchResults>>(DataState.Empty);val state:StateFlow<DataState<SearchResults>> =_state
 private val _geography=MutableStateFlow(GeographyOptions());val geography:StateFlow<GeographyOptions> =_geography
 var query="";private set;var filters=TenderFilters();private set;var sort="relevance";private set
 init{viewModelScope.launch{val p=async{repo.provinces()};val d=async{repo.districts()};val m=async{repo.municipalities()};_geography.value=GeographyOptions((p.await() as? ApiResult.Success)?.value.orEmpty(),(d.await() as? ApiResult.Success)?.value.orEmpty(),(m.await() as? ApiResult.Success)?.value.orEmpty())}}
 fun search(q:String=query,newFilters:TenderFilters=filters,newSort:String=sort)=viewModelScope.launch{query=q;filters=newFilters;sort=newSort;history.add(q);_state.value=DataState.Loading;_state.value=when(val r=repo.search(q,1,newFilters,newSort)){is ApiResult.Success->if(r.value.items.isEmpty())DataState.Empty else DataState.Success(SearchResults(r.value.items,1,r.value.total_pages));is ApiResult.Error->DataState.Error(r.message)}}
 fun loadMore()=viewModelScope.launch{val old=(_state.value as? DataState.Success)?.data?:return@launch;if(old.page>=old.totalPages)return@launch;_state.value=DataState.Success(old.copy(loadingMore=true));when(val r=repo.search(query,old.page+1,filters,sort)){is ApiResult.Success->_state.value=DataState.Success(SearchResults(old.items+r.value.items,r.value.page,r.value.total_pages));is ApiResult.Error->_state.value=DataState.Error(r.message)}}
}
class DetailViewModel(private val id:String,private val repo:TenderRepository):ViewModel(){private val _state=MutableStateFlow<DataState<TenderDetail>>(DataState.Loading);val state:StateFlow<DataState<TenderDetail>> =_state;init{load()};fun load()=viewModelScope.launch{_state.value=DataState.Loading;_state.value=when(val r=repo.detail(id)){is ApiResult.Success->DataState.Success(r.value);is ApiResult.Error->DataState.Error(r.message)}}}
