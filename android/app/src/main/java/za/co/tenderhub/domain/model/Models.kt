package za.co.tenderhub.domain.model
data class User(val id:String,val email:String,val first_name:String,val last_name:String,val phone:String?,val role:String,val status:String)
data class TokenResponse(val access_token:String,val token_type:String,val expires_at:String)
data class RegisterRequest(val email:String,val password:String,val first_name:String,val last_name:String,val phone:String?=null)
data class LoginRequest(val email:String,val password:String)
data class Tender(val id:String,val title:String,val organisation:String,val reference_number:String?,val province:String?,val closing_date:String?,val status:String)
data class Page<T>(val items:List<T>,val page:Int,val page_size:Int,val total:Int)
