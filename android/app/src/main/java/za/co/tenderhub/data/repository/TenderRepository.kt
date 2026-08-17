package za.co.tenderhub.data.repository
import za.co.tenderhub.data.remote.TenderHubApi
import za.co.tenderhub.domain.model.*
interface TenderRepository{suspend fun home():ApiResult<HomeResponse>;suspend fun search(q:String,page:Int,provinceId:String?=null,category:String?=null,sort:String="relevance"):ApiResult<Page<Tender>>;suspend fun detail(id:String):ApiResult<TenderDetail>;suspend fun provinces():ApiResult<List<Province>>}
class NetworkTenderRepository(private val api:TenderHubApi):TenderRepository{override suspend fun home()=apiCall{api.home()};override suspend fun search(q:String,page:Int,provinceId:String?,category:String?,sort:String)=apiCall{api.tenders(q.ifBlank{null},page,20,provinceId,category,null,sort)};override suspend fun detail(id:String)=apiCall{api.tender(id)};override suspend fun provinces()=apiCall{api.provinces()}}
