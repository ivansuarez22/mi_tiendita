{% extends "base.html" %}
{% block content %}
  <div class="row">
    <div class="col-12">
      <h1 class="text-center mb-4">🏪 Bienvenido a la Tiendita</h1>
      <p class="text-center text-muted mb-3">Sistema de gestión de inventario y ventas</p>
      

    </div>
  </div>

  <!-- Estadísticas principales -->
  <div class="row mb-5">
    <div class="col-md-3 mb-3">
      <div class="card text-center h-100">
        <div class="card-body">
          <h5 class="card-title text-primary">📦 Productos</h5>
          <h2 class="card-text">{{ num_products }}</h2>
          <p class="card-text text-muted">Total registrados</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card text-center h-100">
        <div class="card-body">
          <h5 class="card-title text-success">👥 Clientes</h5>
          <h2 class="card-text">{{ num_clients }}</h2>
          <p class="card-text text-muted">Total registrados</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card text-center h-100">
        <div class="card-body">
          <h5 class="card-title text-info">🛒 Pedidos</h5>
          <h2 class="card-text">{{ num_orders }}</h2>
          <p class="card-text text-muted">Total realizados</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card text-center h-100">
        <div class="card-body">
          <h5 class="card-title text-warning">💰 Ventas</h5>
          <h2 class="card-text">${{ "%.2f"|format(total_sales) }}</h2>
          <p class="card-text text-muted">Total generado</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Alertas y notificaciones -->
  {% if low_stock_products > 0 %}
  <div class="row mb-4">
    <div class="col-12">
      <div class="alert alert-warning" role="alert">
        <h5 class="alert-heading">⚠️ Atención: Stock Bajo</h5>
        <p class="mb-0">Hay <strong>{{ low_stock_products }}</strong> producto(s) con stock menor a 10 unidades. 
        {% if session.user_id %}
          <a href="{{ url_for('listar_productos') }}" class="alert-link">Ver productos</a>
        {% endif %}
        </p>
      </div>
    </div>
  </div>
  {% endif %}

  <!-- Accesos rápidos -->
  {% if session.user_id %}
  <div class="row mb-4">
    <div class="col-12">
      <h3 class="mb-3">🚀 Accesos Rápidos</h3>
    </div>
    <div class="col-md-4 mb-3">
      <div class="card">
        <div class="card-body text-center">
          <h5 class="card-title">📦 Gestionar Productos</h5>
          <p class="card-text">Ver, agregar y editar productos del inventario</p>
          <a href="{{ url_for('listar_productos') }}" class="btn btn-primary">Ir a Productos</a>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-3">
      <div class="card">
        <div class="card-body text-center">
          <h5 class="card-title">👥 Gestionar Clientes</h5>
          <p class="card-text">Administrar información de clientes</p>
          <a href="{{ url_for('listar_clientes') }}" class="btn btn-success">Ir a Clientes</a>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-3">
      <div class="card">
        <div class="card-body text-center">
          <h5 class="card-title">🛒 Gestionar Pedidos</h5>
          <p class="card-text">Crear y administrar pedidos de venta</p>
          <a href="{{ url_for('gestionar_pedidos') }}" class="btn btn-info">Ir a Pedidos</a>
        </div>
      </div>
    </div>
  </div>
  {% else %}
  <div class="row">
    <div class="col-12 text-center">
      <h3 class="mb-3">🔐 Acceso al Sistema</h3>
      <p class="mb-4">Para acceder a todas las funcionalidades del sistema, inicia sesión o regístrate</p>
      <a href="{{ url_for('login') }}" class="btn btn-primary me-3">Iniciar Sesión</a>
      <a href="{{ url_for('register') }}" class="btn btn-outline-primary">Registrarse</a>
    </div>
  </div>
  {% endif %}
{% endblock %}
  
