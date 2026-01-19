import os

def identify_project_type(path):
    """
    Identifies the project type based on key files present in the root.
    Returns a dict with 'name' and 'color' (hex).
    """
    if not os.path.isdir(path):
        return {'name': 'File', 'color': '#6B7280'}
        
    try:
        files = set(os.listdir(path))
    except OSError:
        return {'name': 'Folder', 'color': '#6B7280'}
    
    # Priority Checks
    
    # JavaScript / Node Ecosystem
    if 'package.json' in files:
        if 'next.config.js' in files or 'next.config.ts' in files:
             return {'name': 'Next.js', 'color': '#000000'} # Distinctive Black
        if 'tsconfig.json' in files:
             return {'name': 'TypeScript', 'color': '#3178C6'}
        if 'vite.config.js' in files or 'vite.config.ts' in files:
             return {'name': 'Vite', 'color': '#646CFF'}
        return {'name': 'Node.js', 'color': '#339933'}
        
    # Python Ecosystem
    if 'requirements.txt' in files or 'pyproject.toml' in files or 'main.py' in files or 'setup.py' in files:
        if 'manage.py' in files:
            return {'name': 'Django', 'color': '#092E20'}
        if 'flask_app.py' in files or 'app.py' in files:
            # Heuristic only
            return {'name': 'Python', 'color': '#3776AB'} 
        return {'name': 'Python', 'color': '#3776AB'}
        
    # Java
    if 'pom.xml' in files:
        return {'name': 'Java (Maven)', 'color': '#B07219'}
    if 'build.gradle' in files or 'build.gradle.kts' in files:
        return {'name': 'Java (Gradle)', 'color': '#02303A'}
        
    # Go
    if 'go.mod' in files:
        return {'name': 'Go', 'color': '#00ADD8'}
        
    # Rust
    if 'Cargo.toml' in files:
        return {'name': 'Rust', 'color': '#DEA584'}
        
    # PHP / Laravel
    if 'composer.json' in files:
        if 'artisan' in files:
            return {'name': 'Laravel', 'color': '#FF2D20'}
        return {'name': 'PHP', 'color': '#4F5D95'}
        
    # Web (Static)
    if 'index.html' in files:
        return {'name': 'Web', 'color': '#E34F26'}
    
    # C# / .NET
    if any(f.endswith('.sln') or f.endswith('.csproj') for f in files):
        return {'name': 'C# / .NET', 'color': '#178600'}
        
    # Git
    if '.git' in files:
        return {'name': 'Git Repo', 'color': '#F05032'}
        
    return {'name': 'Folder', 'color': '#6B7280'}
