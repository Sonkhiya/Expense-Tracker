  # Spec: Login and Logout                                                                                                                                                                   
                                                                                                                                                                                             
  ## Overview                                                                                                                                                                                
  The Login and Logout feature enables authenticated users to securely access protected areas of the application. This step comes after the database setup and registration features,        
  providing the authentication layer needed to protect user data and create personal accounts. Users will be able to sign in with their registered credentials and sign out when finished.   
                  
  ## Depends on                                                                                                                                                                              
  - Registration (Step 2)
  - Database setup (Step 1)                                                                                                                                                                  
                                                                                                                                                                                             
  ## Routes                                                                                                                                                                                  
  - `GET /login` — Render login form — public                                                                                                                                                
  - `POST /login` — Process login and set session — public                                                                                                                                   
  - `GET /logout` — Clear session and redirect to login — logged-in only                                                                                                                     
  - `GET /dashboard` — Protected area requiring authentication — logged-in only                                                                                                              
                                                                                                                                                                                             
  ## Database changes                                                                                                                                                                        
  No database changes. Authentication will use existing user table from registration step.                                                                                                   
                                                                                                                                                                                             
  ## Templates                                                                                                                                                                               
  **Create:**                                                                                                                                                                                
  - `templates/login.html` — Login form with username/email and password fields                                                                                                              
  - `templates/login_success.html` — Success message after login                                                                                                                             
  - `templates/logout_success.html` — Success message after logout                                                                                                                           
                                                                                                                                                                                             
  **Modify:**                                                                                                                                                                                
  - `templates/base.html` — Add logout button in navigation when user is logged in, hide navigation when anonymous                                                                           
                                                                                                                                                                                             
  ## Files to change                                                                                                                                                                         
  - `app.py` — Add login/logout/dashboard routes                                                                                                                                             
  - `templates/base.html` — Add user authentication UI elements                                                                                                                              
                                                                                                                                                                                             
  ## Files to create                                                                                                                                                                         
  - `templates/login.html`                                                                                                                                                                   
  - `templates/login_success.html`                                                                                                                                                           
  - `templates/logout_success.html`                                                                                                                                                          
  - `templates/user_dashboard.html`                                                                                                                                                          
                                                                                                                                                                                             
  ## New dependencies                                                                                                                                                                        
  No new dependencies. Use existing Flask, Werkzeug for password hashing.                                                                                                                    
                                                                                                                                                                                             
  ## Rules for implementation                                                                                                                                                                
  - No SQLAlchemy or ORMs — use raw SQL with parameterised queries                                                                                                                           
  - Passwords hashed with werkzeug.security.generate_password_hash and check_password_hash                                                                                                   
  - All templates extend `base.html`                                                                                                                                                         
  - Session management using Flask's built-in session (secure cookies)                                                                                                                       
  - Use CSS variables — never hardcode hex values                                                                                                                                            
  - Redirect to dashboard after successful login                                                                                                                                             
  - Clear session data on logout                                                                                                                                                             
  - Implement CSRF protection for POST routes                                                                                                                                                
                                                                                                                                                                                             
  ## Definition of done                                                                                                                                                                      
  - [ ] `/login` page displays login form                                                                                                                                                    
  - [ ] `/dashboard` is accessible only when logged in                                                                                                                                       
  - [ ] `/login` redirects to `/dashboard` on successful authentication                                                                                                                      
  - [ ] `/logout` clears session and redirects to `/login`                                                                                                                                   
  - [ ] Failed login attempts show appropriate error message                                                                                                                                 
  - [ ] Session cannot be exploited (secure cookies enabled)                                                                                                                                 
  - [ ] CSRF tokens present on POST login/logout forms                                                                                                                                       
  - [ ] Base template shows/hides navigation based on auth state                                                                                                                             
  SPEC_EOF     