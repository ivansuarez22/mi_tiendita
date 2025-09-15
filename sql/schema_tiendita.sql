-- Ejecutar conectado a tiendita_db
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  rol TEXT NOT NULL CHECK (rol IN ('admin','empleado'))
);

CREATE TABLE IF NOT EXISTS clientes (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  correo TEXT
);

CREATE TABLE IF NOT EXISTS productos (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  precio NUMERIC(10,2) NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pedidos (
  id SERIAL PRIMARY KEY,
  cliente_id INTEGER REFERENCES clientes(id),
  producto_id INTEGER REFERENCES productos(id),
  cantidad INTEGER NOT NULL CHECK (cantidad > 0),
  precio_unitario NUMERIC(10,2) NOT NULL,
  total NUMERIC(12,2) NOT NULL,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS devoluciones (
  id SERIAL PRIMARY KEY,
  pedido_id INTEGER REFERENCES pedidos(id),
  motivo TEXT,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE OR REPLACE PROCEDURE registrar_pedido(
  p_cliente_id INT,
  p_producto_id INT,
  p_cantidad INT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_precio NUMERIC(10,2);
  v_stock INTEGER;
  v_total NUMERIC(12,2);
BEGIN
  SELECT precio, stock INTO v_precio, v_stock FROM productos WHERE id = p_producto_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Producto % no existe', p_producto_id;
  END IF;
  IF v_stock < p_cantidad THEN
    RAISE EXCEPTION 'Stock insuficiente: % < %', v_stock, p_cantidad;
  END IF;
  v_total := v_precio * p_cantidad;
  INSERT INTO pedidos (cliente_id, producto_id, cantidad, precio_unitario, total)
    VALUES (p_cliente_id, p_producto_id, p_cantidad, v_precio, v_total);
END;
$$;

CREATE OR REPLACE FUNCTION ventas_totales()
RETURNS NUMERIC
LANGUAGE sql
AS $$
  SELECT COALESCE(SUM(total),0) FROM pedidos;
$$;

CREATE OR REPLACE FUNCTION actualizar_stock_func()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE productos SET stock = stock - NEW.cantidad WHERE id = NEW.producto_id;
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE productos SET stock = stock + OLD.cantidad WHERE id = OLD.producto_id;
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    IF OLD.producto_id = NEW.producto_id THEN
      UPDATE productos SET stock = stock + OLD.cantidad - NEW.cantidad WHERE id = NEW.producto_id;
    ELSE
      UPDATE productos SET stock = stock + OLD.cantidad WHERE id = OLD.producto_id;
      UPDATE productos SET stock = stock - NEW.cantidad WHERE id = NEW.producto_id;
    END IF;
    RETURN NEW;
  END IF;
END;
$$;

DROP TRIGGER IF EXISTS actualizar_stock ON pedidos;
CREATE TRIGGER actualizar_stock
  AFTER INSERT OR DELETE OR UPDATE ON pedidos
  FOR EACH ROW
  EXECUTE FUNCTION actualizar_stock_func();

GRANT SELECT, UPDATE, DELETE ON TABLE productos, clientes, pedidos, devoluciones TO tiendita_empleado;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiendita_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tiendita_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, UPDATE, DELETE ON TABLES TO tiendita_empleado;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tiendita_app;
